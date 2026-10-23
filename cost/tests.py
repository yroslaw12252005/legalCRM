from datetime import date, datetime
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from contract.models import Contract
from felial.models import Felial
from leads.models import Record

from .models import Surcharge


class MonthlySalaryCalculationTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Компания")
        self.other_company = Companys.objects.create(title="Другая компания")
        self.branch = Felial.objects.create(title="Главный", cites="Москва", companys=self.company)
        self.other_branch = Felial.objects.create(
            title="Главный",
            cites="Тула",
            companys=self.other_company,
        )
        self.admin = User.objects.create_user(
            username="salary_admin",
            password="password",
            status="Администратор",
            companys=self.company,
            felial=self.branch,
        )
        self.lawyer = User.objects.create_user(
            username="salary_lawyer",
            password="password",
            status="Юрист пирвичник",
            type_zp="Процент",
            percent=Decimal("0.100"),
            bet=0,
            companys=self.company,
            felial=self.branch,
        )
        self.record = Record.objects.create(
            name="Клиент",
            employees_UPP=self.lawyer.username,
            companys=self.company,
            felial=self.branch,
        )
        self.contract = Contract.objects.create(
            record=self.record,
            number="1001",
            amount=Decimal("100000"),
            initial_payment=Decimal("50000"),
            contract_date=date(2026, 10, 5),
        )
        previous_contract = Contract.objects.create(
            record=self.record,
            number="1000",
            amount=Decimal("60000"),
            initial_payment=Decimal("30000"),
            contract_date=date(2026, 9, 30),
        )
        Surcharge.objects.create(
            contract=self.contract,
            cost=Decimal("25000"),
            dat=datetime(2026, 10, 15, 12, 0),
            is_paid=True,
            paid_at=datetime(2026, 10, 20, 10, 0),
        )
        Surcharge.objects.create(
            contract=self.contract,
            cost=Decimal("25000"),
            dat=datetime(2026, 10, 25, 12, 0),
            is_paid=False,
        )
        Surcharge.objects.create(
            contract=previous_contract,
            cost=Decimal("5000"),
            dat=datetime(2026, 10, 7, 12, 0),
            is_paid=True,
            paid_at=None,
        )
        Surcharge.objects.create(
            contract=previous_contract,
            cost=Decimal("7000"),
            dat=datetime(2026, 10, 30, 12, 0),
            is_paid=True,
            paid_at=datetime(2026, 11, 1, 9, 0),
        )
        self.client.force_login(self.admin)

    def test_salary_uses_monthly_initial_payments_and_paid_surcharges(self):
        response = self.client.get(
            reverse("user_inform", args=[self.lawyer.id]),
            {"month": "2026-10"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["initial_payments"], Decimal("50000"))
        self.assertEqual(response.context["surcharge_payments"], Decimal("30000"))
        self.assertEqual(response.context["base_total"], Decimal("80000"))
        self.assertEqual(response.context["zp"], Decimal("8000.000"))
        self.assertEqual(response.context["contracts_count"], 1)
        self.assertEqual(response.context["surcharges_count"], 2)
        self.assertContains(response, "Октябрь 2026")

    def test_paid_surcharge_is_counted_by_confirmation_month(self):
        response = self.client.get(
            reverse("user_inform", args=[self.lawyer.id]),
            {"month": "2026-11"},
        )

        self.assertEqual(response.context["initial_payments"], Decimal("0"))
        self.assertEqual(response.context["surcharge_payments"], Decimal("7000"))
        self.assertEqual(response.context["base_total"], Decimal("7000"))
        self.assertEqual(response.context["zp"], Decimal("700.000"))

    def test_salary_page_does_not_open_employee_from_another_company(self):
        other_employee = User.objects.create_user(
            username="other_salary_employee",
            password="password",
            status="Оператор",
            type_zp="Ставка",
            bet=50000,
            companys=self.other_company,
            felial=self.other_branch,
        )

        response = self.client.get(reverse("user_inform", args=[other_employee.id]))

        self.assertEqual(response.status_code, 404)
