from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.models import Record


class CurrentApplicationsTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Company")
        self.felial = Felial.objects.create(title="Main", cites="Moscow", companys=self.company)
        self.user = User.objects.create_user(
            username="director_1",
            password="test-pass-123",
            status="Директор КЦ",
            companys=self.company,
            felial=self.felial,
        )

    def test_login_redirects_to_current_applications(self):
        response = self.client.post(
            reverse("all_leads"),
            {"username": "director_1", "password": "test-pass-123"},
        )
        self.assertRedirects(response, reverse("current_applications"))

    def test_current_applications_shows_only_today_records(self):
        today_record = Record.objects.create(
            name="Today lead",
            phone="+70000000001",
            description="today",
            companys=self.company,
            felial=self.felial,
        )
        old_record = Record.objects.create(
            name="Old lead",
            phone="+70000000002",
            description="old",
            companys=self.company,
            felial=self.felial,
        )
        Record.objects.filter(id=old_record.id).update(created_at=timezone.now() - timedelta(days=1))

        self.client.force_login(self.user)
        response = self.client.get(reverse("current_applications"))

        self.assertEqual(response.status_code, 200)
        records = list(response.context["records"])
        self.assertIn(today_record, records)
        self.assertNotIn(old_record, records)
