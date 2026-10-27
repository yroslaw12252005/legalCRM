from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from contract.models import Contract
from felial.models import Felial
from leads.models import Record
from smart_calendar.models import Booking


class AllLeadsBulkActionsTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Company")
        self.felial = Felial.objects.create(title="Main", cites="Moscow", companys=self.company)
        self.admin = User.objects.create_user(
            username="admin",
            password="test-pass-123",
            status="Администратор",
            companys=self.company,
            felial=self.felial,
        )
        self.record = Record.objects.create(
            name="Client",
            phone="+70000000001",
            description="desc",
            companys=self.company,
            felial=self.felial,
            status="Новая",
        )

    def test_bulk_status_change_updates_selected_records(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("all_leads_bulk_in_work"),
            data={
                "action": "change_status",
                "bulk_status": "Онлайн",
                "selected_records": [self.record.id],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, "Онлайн")

    def test_admin_can_open_lead_exchange_placeholder(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("lead_exchange"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Биржа заявок")
        self.assertContains(response, "Потоковое получение лидов")
        self.assertContains(response, "Активные аукционы")
        self.assertContains(response, "Демонстрационный режим")

    def test_admin_can_open_lead_exchange_lot_preview(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("lead_exchange_lot_preview", args=["bankruptcy-msk-100"])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Компании-участники")
        self.assertContains(response, "Отправить предложение")

    def test_non_admin_cannot_open_lead_exchange_lot_preview(self):
        manager = User.objects.create_user(
            username="exchange_manager",
            password="test-pass-123",
            status="Менеджер",
            companys=self.company,
            felial=self.felial,
        )
        self.client.force_login(manager)

        response = self.client.get(
            reverse("lead_exchange_lot_preview", args=["bankruptcy-msk-100"])
        )

        self.assertRedirects(response, reverse("all_leads"))


class AllLeadsPhoneVisibilityTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Company")
        self.felial = Felial.objects.create(title="Main", cites="Moscow", companys=self.company)
        self.record = Record.objects.create(
            name="Client",
            phone="+70000000001",
            description="desc",
            companys=self.company,
            felial=self.felial,
            in_work=True,
            status="Онлайн",
        )

    def test_manager_sees_dash_until_client_came(self):
        manager = User.objects.create_user(
            username="manager",
            password="test-pass-123",
            status="Менеджер",
            companys=self.company,
            felial=self.felial,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("all_leads"))

        self.assertContains(response, "-")
        self.assertNotContains(response, "+70000000001")

    def test_manager_sees_phone_after_client_came(self):
        manager = User.objects.create_user(
            username="manager",
            password="test-pass-123",
            status="Менеджер",
            companys=self.company,
            felial=self.felial,
        )
        Booking.objects.create(
            client=self.record,
            companys=self.company,
            felial=self.felial,
            come=True,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("all_leads"))

        self.assertContains(response, "+70000000001")

    def test_director_upp_sees_phone_for_online_status(self):
        director = User.objects.create_user(
            username="upp_director",
            password="test-pass-123",
            status="Директор ЮПП",
            companys=self.company,
            felial=self.felial,
        )
        self.client.force_login(director)

        response = self.client.get(reverse("all_leads"))
        self.assertContains(response, "+70000000001")

    def test_director_upp_sees_phone_after_client_came(self):
        director = User.objects.create_user(
            username="upp_director",
            password="test-pass-123",
            status="Директор ЮПП",
            companys=self.company,
            felial=self.felial,
        )
        self.record.status = "Запись в офис"
        self.record.save(update_fields=["status"])
        self.client.force_login(director)

        response = self.client.get(reverse("all_leads"))
        self.assertContains(response, "-")
        self.assertNotContains(response, "+70000000001")

        Booking.objects.create(
            client=self.record,
            companys=self.company,
            felial=self.felial,
            come=True,
        )
        response = self.client.get(reverse("all_leads"))
        self.assertContains(response, "+70000000001")

    def test_contract_phone_is_visible_and_transfer_allowed(self):
        director = User.objects.create_user(
            username="upp_director",
            password="test-pass-123",
            status="Директор ЮПП",
            companys=self.company,
            felial=self.felial,
        )
        self.record.status = "Договор"
        self.record.save(update_fields=["status"])
        self.client.force_login(director)

        list_response = self.client.get(reverse("all_leads"))
        record_response = self.client.get(reverse("record", args=[self.record.id]))

        self.assertContains(list_response, "+70000000001")
        self.assertContains(record_response, "Передать представителям")


class AllLeadsFiltersTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Company")
        self.felial = Felial.objects.create(title="Main", cites="Moscow", companys=self.company)
        self.admin = User.objects.create_user(
            username="admin_filter",
            password="test-pass-123",
            status="Администратор",
            companys=self.company,
            felial=self.felial,
        )
        self.unassigned_record = Record.objects.create(
            name="Unassigned Lead",
            phone="+70000000001",
            description="desc",
            companys=self.company,
            felial=self.felial,
            where="Право",
        )
        self.assigned_record = Record.objects.create(
            name="Assigned Lead",
            phone="+70000000002",
            description="desc",
            companys=self.company,
            felial=self.felial,
            employees_KC="operator_1",
            employees_UPP="lawyer_1",
            where="Марина",
        )
        self.operator = User.objects.create_user(
            username="operator_1",
            password="test-pass-123",
            status="Оператор",
            companys=self.company,
            felial=self.felial,
        )
        self.lawyer = User.objects.create_user(
            username="lawyer_1",
            password="test-pass-123",
            status="Юрист пирвичник",
            companys=self.company,
            felial=self.felial,
        )
        self.representative = User.objects.create_user(
            username="representative_1",
            password="test-pass-123",
            status="Представитель",
            companys=self.company,
            felial=self.felial,
        )
        self.assigned_record.employees_REP = self.representative.username
        self.assigned_record.save(update_fields=["employees_REP"])

    def test_admin_can_filter_unassigned_operators(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("all_leads"), {"operator_state": "unassigned"})

        self.assertContains(response, "Unassigned Lead")
        self.assertNotContains(response, "Assigned Lead")

    def test_admin_can_filter_unassigned_lawyers(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("all_leads"), {"lawyer_state": "unassigned"})

        self.assertContains(response, "Unassigned Lead")
        self.assertNotContains(response, "Assigned Lead")

    def test_search_finds_lead_by_contract_number(self):
        Contract.objects.create(
            record=self.assigned_record,
            number="987654321",
            amount="100000.00",
            initial_payment="10000.00",
            contract_date=date.today(),
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("all_leads"), {"q": "987654321"})

        self.assertContains(response, "Assigned Lead")
        self.assertNotContains(response, "Unassigned Lead")

    def test_search_view_finds_lead_by_contract_number(self):
        Contract.objects.create(
            record=self.assigned_record,
            number="123456789",
            amount="100000.00",
            initial_payment="10000.00",
            contract_date=date.today(),
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("search"), {"q": "123456789"})

        self.assertContains(response, "Assigned Lead")
        self.assertNotContains(response, "Unassigned Lead")

    def test_role_filters_use_their_record_fields(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("all_leads"),
            {
                "operator": self.operator.username,
                "lawyer_upp": self.lawyer.username,
                "lawyer_op": self.representative.username,
            },
        )

        self.assertContains(response, "Assigned Lead")
        self.assertNotContains(response, "Unassigned Lead")

    def test_employee_choices_are_split_by_role_and_company(self):
        other_company = Companys.objects.create(title="Other company")
        other_branch = Felial.objects.create(title="Other", cites="Tula", companys=other_company)
        User.objects.create_user(
            username="foreign_operator",
            password="test-pass-123",
            status="Оператор",
            companys=other_company,
            felial=other_branch,
        )
        secondary_lawyer = User.objects.create_user(
            username="secondary_lawyer",
            password="test-pass-123",
            status="ОП",
            companys=self.company,
            felial=self.felial,
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("all_leads"))

        self.assertQuerySetEqual(response.context["operators"], [self.operator])
        self.assertQuerySetEqual(response.context["lawyers"], [self.lawyer])
        self.assertQuerySetEqual(response.context["representatives"], [self.representative])
        self.assertNotIn(secondary_lawyer, response.context["lawyers"])


class StatusPermissionsTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Company")
        self.felial = Felial.objects.create(title="Main", cites="Moscow", companys=self.company)
        self.record = Record.objects.create(
            name="Client",
            phone="+70000000001",
            description="desc",
            companys=self.company,
            felial=self.felial,
            in_work=True,
            status="Новая",
        )

    def test_lawyer_primary_cannot_set_contract_in_bulk(self):
        lawyer = User.objects.create_user(
            username="lawyer",
            password="test-pass-123",
            status="Юрист пирвичник",
            companys=self.company,
            felial=self.felial,
        )
        self.record.employees_UPP = lawyer.username
        self.record.save(update_fields=["employees_UPP"])
        self.client.force_login(lawyer)

        response = self.client.post(
            reverse("all_leads_bulk_in_work"),
            data={
                "action": "change_status",
                "bulk_status": "Договор",
                "selected_records": [self.record.id],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, "Новая")

    def test_manager_can_set_contract_in_bulk(self):
        manager = User.objects.create_user(
            username="manager",
            password="test-pass-123",
            status="Менеджер",
            companys=self.company,
            felial=self.felial,
        )
        self.client.force_login(manager)

        response = self.client.post(
            reverse("all_leads_bulk_in_work"),
            data={
                "action": "change_status",
                "bulk_status": "Договор",
                "selected_records": [self.record.id],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, "Договор")
