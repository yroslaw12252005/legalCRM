from django.test import TestCase
from django.urls import reverse

from company.models import Companys
from felial.models import Felial
from leads.models import Record

from .models import User


class EmployeeDeactivationTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Компания")
        self.branch = Felial.objects.create(
            title="Главный",
            cites="Москва",
            companys=self.company,
        )
        self.admin = User.objects.create_user(
            username="admin",
            password="test-pass-123",
            status="Администратор",
            companys=self.company,
            felial=self.branch,
        )
        self.lawyer = User.objects.create_user(
            username="lawyer",
            password="test-pass-123",
            status="Юрист пирвичник",
            companys=self.company,
            felial=self.branch,
        )
        self.record = Record.objects.create(
            name="Клиент",
            companys=self.company,
            felial=self.branch,
            lawyer=self.lawyer,
            employees_UPP=self.lawyer.username,
        )

    def test_delete_employee_deactivates_and_preserves_assignment(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse("delete_employee", args=[self.lawyer.id]))

        self.assertEqual(response.status_code, 302)
        self.lawyer.refresh_from_db()
        self.record.refresh_from_db()
        self.assertFalse(self.lawyer.is_active)
        self.assertEqual(self.record.lawyer_id, self.lawyer.id)
        self.assertEqual(self.record.employees_UPP, self.lawyer.username)
