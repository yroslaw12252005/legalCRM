from datetime import datetime
from decimal import Decimal

from django.db.models import Sum
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from cost.models import Surcharge
from felial.models import Felial
from leads.models import Record

from .forms import ContractForm
from .models import Contract


class ContractFlowTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Компания")
        self.other_company = Companys.objects.create(title="Другая компания")
        self.branch = Felial.objects.create(title="Главный", cites="Москва", companys=self.company)
        self.other_branch = Felial.objects.create(title="Главный", cites="Москва", companys=self.other_company)
        self.manager = User.objects.create_user(
            username="manager",
            password="password",
            status="Менеджер",
            companys=self.company,
            felial=self.branch,
        )
        self.operator = User.objects.create_user(
            username="operator",
            password="password",
            status="Оператор",
            companys=self.company,
            felial=self.branch,
        )
        self.admin = User.objects.create_user(
            username="admin",
            password="password",
            status="Администратор",
            companys=self.company,
            felial=self.branch,
        )
        self.record = Record.objects.create(
            name="Клиент",
            companys=self.company,
            felial=self.branch,
        )
        self.other_record = Record.objects.create(
            name="Чужой клиент",
            companys=self.other_company,
            felial=self.other_branch,
        )

    def contract_data(
        self,
        surcharge_cost="80000.00",
        surcharge_id="",
        initial_forms="0",
        **overrides,
    ):
        data = {
            "number": "12345",
            "amount": "100000.00",
            "initial_payment": "20000.00",
            "contract_date": "2026-10-21",
            "surcharges-TOTAL_FORMS": "1",
            "surcharges-INITIAL_FORMS": initial_forms,
            "surcharges-MIN_NUM_FORMS": "0",
            "surcharges-MAX_NUM_FORMS": "1000",
            "surcharges-0-id": surcharge_id,
            "surcharges-0-cost": surcharge_cost,
            "surcharges-0-date": "2026-10-25",
            "surcharges-0-time": "10:30",
        }
        data.update(overrides)
        return data

    def test_manager_can_create_and_edit_contract(self):
        self.client.force_login(self.manager)
        response = self.client.post(reverse("add_contract", args=[self.record.id]), self.contract_data())
        self.assertRedirects(response, reverse("record", args=[self.record.id]))

        contract = Contract.objects.get(record=self.record)
        self.assertEqual(contract.number, "12345")
        self.assertEqual(contract.amount, Decimal("100000.00"))
        surcharge = contract.surcharges.get()
        self.assertEqual(surcharge.cost, Decimal("80000.00"))
        self.assertEqual(surcharge.responsible, self.manager)

        response = self.client.post(
            reverse("edit_contract", args=[contract.id]),
            self.contract_data(
                amount="120000.00",
                surcharge_cost="100000.00",
                surcharge_id=str(surcharge.id),
                initial_forms="1",
            ),
        )
        self.assertRedirects(response, reverse("record", args=[self.record.id]))
        contract.refresh_from_db()
        self.assertEqual(contract.amount, Decimal("120000.00"))
        surcharge.refresh_from_db()
        self.assertEqual(surcharge.cost, Decimal("100000.00"))

    def test_contract_is_not_created_when_surcharges_do_not_cover_remaining_amount(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("add_contract", args=[self.record.id]),
            self.contract_data(surcharge_cost="70000.00"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сумма доплат должна быть равна остатку")
        self.assertFalse(Contract.objects.filter(record=self.record).exists())
        self.assertFalse(Surcharge.objects.exists())

    def test_contract_can_be_created_with_multiple_surcharges(self):
        data = self.contract_data(surcharge_cost="30000.00")
        data.update(
            {
                "surcharges-TOTAL_FORMS": "2",
                "surcharges-1-cost": "50000.00",
                "surcharges-1-date": "2026-11-25",
                "surcharges-1-time": "11:00",
            }
        )
        self.client.force_login(self.manager)

        response = self.client.post(reverse("add_contract", args=[self.record.id]), data)

        self.assertRedirects(response, reverse("record", args=[self.record.id]))
        contract = Contract.objects.get(record=self.record)
        self.assertEqual(contract.surcharges.count(), 2)
        self.assertEqual(
            contract.surcharges.aggregate(total=Sum("cost"))["total"],
            Decimal("80000.00"),
        )

    def test_contract_with_full_initial_payment_does_not_require_surcharges(self):
        data = self.contract_data(amount="100000.00", initial_payment="100000.00", surcharge_cost="")
        data["surcharges-0-date"] = ""
        data["surcharges-0-time"] = ""
        self.client.force_login(self.manager)

        response = self.client.post(reverse("add_contract", args=[self.record.id]), data)

        self.assertRedirects(response, reverse("record", args=[self.record.id]))
        contract = Contract.objects.get(record=self.record)
        self.assertFalse(contract.surcharges.exists())

    def test_operator_cannot_create_contract(self):
        self.client.force_login(self.operator)
        response = self.client.post(reverse("add_contract", args=[self.record.id]), self.contract_data())
        self.assertRedirects(response, reverse("record", args=[self.record.id]))
        self.assertFalse(Contract.objects.filter(record=self.record).exists())

    def test_contract_access_is_limited_to_user_company(self):
        contract = Contract.objects.create(
            record=self.other_record,
            number="99",
            amount=100,
            initial_payment=10,
            contract_date="2026-10-21",
        )
        self.client.force_login(self.manager)
        response = self.client.get(reverse("edit_contract", args=[contract.id]))
        self.assertEqual(response.status_code, 404)

    def test_initial_payment_cannot_exceed_contract_amount(self):
        form = ContractForm(data=self.contract_data(amount="100", initial_payment="101"))
        self.assertFalse(form.is_valid())
        self.assertIn("initial_payment", form.errors)

    def test_contract_number_must_be_unique_for_record(self):
        Contract.objects.create(
            record=self.record,
            number="12345",
            amount=100000,
            initial_payment=20000,
            contract_date="2026-10-20",
        )
        form = ContractForm(
            data=self.contract_data(),
            instance=Contract(record=self.record),
        )
        self.assertFalse(form.is_valid())
        self.assertIn("number", form.errors)

    def test_surcharge_is_created_for_selected_contract(self):
        contract = Contract.objects.create(
            record=self.record,
            number="12345",
            amount=100000,
            initial_payment=20000,
            contract_date="2026-10-21",
        )
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("cost", args=[contract.id]),
            {"cost": "10000", "date": "2026-10-25", "time": "10:30"},
        )
        self.assertRedirects(response, reverse("record", args=[self.record.id]))
        surcharge = Surcharge.objects.get(contract=contract)
        self.assertEqual(surcharge.cost, Decimal("10000"))
        self.assertEqual(surcharge.dat, datetime(2026, 10, 25, 10, 30))
        self.assertEqual(surcharge.responsible, self.manager)

    def test_record_page_groups_surcharges_under_contract(self):
        contract = Contract.objects.create(
            record=self.record,
            number="12345",
            amount=100000,
            initial_payment=20000,
            contract_date="2026-10-21",
        )
        Surcharge.objects.create(
            contract=contract,
            cost=10000,
            dat=datetime(2026, 10, 25, 10, 30),
            responsible=self.manager,
        )
        self.client.force_login(self.manager)
        response = self.client.get(reverse("record", args=[self.record.id]))
        self.assertContains(response, "12345")
        self.assertContains(response, "100000")
        self.assertContains(response, "10000")
        self.assertContains(response, "Осталось внести")
        self.assertContains(response, "Внесено")

    def test_manager_can_mark_surcharge_as_paid(self):
        contract = Contract.objects.create(
            record=self.record,
            number="12345",
            amount=100000,
            initial_payment=20000,
            contract_date="2026-10-21",
        )
        surcharge = Surcharge.objects.create(
            contract=contract,
            cost=80000,
            dat=datetime(2026, 10, 25, 10, 30),
            responsible=self.manager,
        )
        self.client.force_login(self.manager)

        response = self.client.post(reverse("mark_surcharge_paid", args=[surcharge.id]))

        self.assertRedirects(response, reverse("record", args=[self.record.id]))
        surcharge.refresh_from_db()
        self.assertTrue(surcharge.is_paid)
        self.assertEqual(surcharge.paid_by, self.manager)
        self.assertIsNotNone(surcharge.paid_at)

        card_response = self.client.get(reverse("record", args=[self.record.id]))
        self.assertContains(card_response, '<tr class="surcharge-paid">')

    def test_admin_can_mark_surcharge_as_paid(self):
        contract = Contract.objects.create(
            record=self.record,
            number="12345",
            amount=100000,
            initial_payment=20000,
            contract_date="2026-10-21",
        )
        surcharge = Surcharge.objects.create(
            contract=contract,
            cost=80000,
            dat=datetime(2026, 10, 25, 10, 30),
            responsible=self.manager,
        )
        self.client.force_login(self.admin)

        response = self.client.post(reverse("mark_surcharge_paid", args=[surcharge.id]))

        self.assertRedirects(response, reverse("record", args=[self.record.id]))
        surcharge.refresh_from_db()
        self.assertTrue(surcharge.is_paid)
        self.assertEqual(surcharge.paid_by, self.admin)

    def test_operator_cannot_mark_surcharge_as_paid(self):
        contract = Contract.objects.create(
            record=self.record,
            number="12345",
            amount=100000,
            initial_payment=20000,
            contract_date="2026-10-21",
        )
        surcharge = Surcharge.objects.create(
            contract=contract,
            cost=80000,
            dat=datetime(2026, 10, 25, 10, 30),
            responsible=self.manager,
        )
        self.client.force_login(self.operator)

        response = self.client.post(reverse("mark_surcharge_paid", args=[surcharge.id]))

        self.assertRedirects(response, reverse("all_leads"))
        surcharge.refresh_from_db()
        self.assertFalse(surcharge.is_paid)

    def test_paid_confirmation_is_limited_to_user_company(self):
        contract = Contract.objects.create(
            record=self.other_record,
            number="99",
            amount=100,
            initial_payment=10,
            contract_date="2026-10-21",
        )
        surcharge = Surcharge.objects.create(
            contract=contract,
            cost=90,
            dat=datetime(2026, 10, 25, 10, 30),
            responsible=None,
        )
        self.client.force_login(self.manager)

        response = self.client.post(reverse("mark_surcharge_paid", args=[surcharge.id]))

        self.assertEqual(response.status_code, 404)
        surcharge.refresh_from_db()
        self.assertFalse(surcharge.is_paid)

