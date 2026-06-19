from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
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
