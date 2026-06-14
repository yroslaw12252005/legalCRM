from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.models import Record


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
