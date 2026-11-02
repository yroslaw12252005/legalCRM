from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from felial.models import Felial
from leads.models import Record

from .models import Companys


class CompanyWorkModeTests(TestCase):
    def _register_company_and_admin(self, work_mode, suffix):
        response = self.client.post(
            reverse("reg_company"),
            {"title": f"Компания {suffix}", "work_mode": work_mode},
        )
        self.assertEqual(response.status_code, 302)
        company = Companys.objects.get(title=f"Компания {suffix}")

        response = self.client.post(
            reverse("reg_admin_user", args=[company.id]),
            {
                "username": f"Администратор {suffix}",
                "email": f"{suffix}@example.com",
                "password1": "safe-test-pass-123",
                "password2": "safe-test-pass-123",
            },
        )
        self.assertEqual(response.status_code, 302)
        return company, User.objects.get(companys=company)

    def test_solo_registration_creates_one_admin_and_main_branch(self):
        company, admin = self._register_company_and_admin(Companys.MODE_SOLO, "solo")

        self.assertTrue(company.is_solo)
        self.assertEqual(User.objects.filter(companys=company).count(), 1)
        self.assertEqual(admin.status, "Администратор")
        self.assertIsNotNone(admin.felial_id)
        self.assertEqual(admin.felial.title, "Основной")
        self.assertEqual(Felial.objects.filter(companys=company).count(), 1)

    def test_registration_page_offers_solo_and_team_modes(self):
        response = self.client.get(reverse("reg_company"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Самостоятельная работа")
        self.assertContains(response, "Компания с отделами")

    def test_team_registration_keeps_existing_structure_flow(self):
        company, admin = self._register_company_and_admin(Companys.MODE_TEAM, "team")

        self.assertFalse(company.is_solo)
        self.assertIsNone(admin.felial_id)
        self.assertFalse(Felial.objects.filter(companys=company).exists())

    def test_new_solo_lead_is_assigned_to_only_admin(self):
        company, admin = self._register_company_and_admin(Companys.MODE_SOLO, "lead")

        record = Record.objects.create(
            name="Клиент",
            companys=company,
            felial=admin.felial,
        )

        self.assertEqual(record.lawyer_id, admin.id)
        self.assertEqual(record.employees_UPP, admin.username)

    def test_solo_admin_cannot_create_additional_users_or_branches(self):
        company, admin = self._register_company_and_admin(Companys.MODE_SOLO, "limits")
        self.client.force_login(admin)

        employee_response = self.client.get(reverse("reg"))
        branch_response = self.client.get(reverse("add_felial"))

        self.assertEqual(employee_response.status_code, 302)
        self.assertEqual(branch_response.status_code, 302)

        dashboard_response = self.client.get(reverse("current_applications"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertNotContains(dashboard_response, "Добавить пользователя")
        self.assertNotContains(dashboard_response, "Создать филиал")
