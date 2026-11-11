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
        self.assertContains(dashboard_response, "Мой профиль")
        self.assertNotContains(dashboard_response, "Добавить пользователя")
        self.assertNotContains(dashboard_response, "Создать филиал")

    def test_solo_admin_can_update_own_profile_and_password(self):
        company, admin = self._register_company_and_admin(Companys.MODE_SOLO, "profile")
        branch_id = admin.felial_id

        response = self.client.post(
            reverse("update_profile"),
            {
                "username": "Новое Имя",
                "email": "new-profile@example.com",
                "password": "new-safe-pass-456",
            },
        )

        self.assertEqual(response.status_code, 302)
        admin.refresh_from_db()
        self.assertEqual(admin.username, "Новое Имя")
        self.assertEqual(admin.email, "new-profile@example.com")
        self.assertEqual(admin.felial_id, branch_id)
        self.assertEqual(admin.status, "Администратор")
        self.assertTrue(admin.check_password("new-safe-pass-456"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), admin.id)


class CompanyManagementTests(TestCase):
    def setUp(self):
        self.service_company = Companys.objects.create(title="Служебная компания")
        self.target_company = Companys.objects.create(title="Компания клиента")
        self.manager = User.objects.create_user(
            username="Yrik",
            email="yrik@gmail.com",
            password="manager-pass-123",
            status="Администратор",
            companys=self.service_company,
        )
        self.target_admin = User.objects.create_user(
            username="Администратор клиента",
            email="admin-client@example.com",
            password="old-admin-pass-123",
            status="Администратор",
            companys=self.target_company,
        )

    def test_manager_sees_company_actions_and_admin(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("companys"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Компания клиента")
        self.assertContains(response, "admin-client@example.com")
        self.assertContains(response, "Восстановить пароль")
        self.assertContains(response, "Удалить компанию")

    def test_manager_can_reset_company_admin_password(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("reset_company_admin_password", args=[self.target_company.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        credentials = response.context["reset_credentials"]
        self.assertEqual(credentials["email"], self.target_admin.email)
        self.assertEqual(len(credentials["password"]), 16)
        self.target_admin.refresh_from_db()
        self.assertTrue(self.target_admin.check_password(credentials["password"]))
        self.assertFalse(self.target_admin.check_password("old-admin-pass-123"))

        next_response = self.client.get(reverse("companys"))
        self.assertIsNone(next_response.context["reset_credentials"])
        self.assertNotContains(next_response, credentials["password"])

    def test_manager_can_delete_another_company(self):
        record = Record.objects.create(
            name="Клиент удаляемой компании",
            companys=self.target_company,
        )
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("delete_company", args=[self.target_company.id]),
        )

        self.assertRedirects(response, reverse("companys"))
        self.assertFalse(Companys.objects.filter(pk=self.target_company.id).exists())
        self.assertFalse(User.objects.filter(pk=self.target_admin.id).exists())
        self.assertFalse(Record.objects.filter(pk=record.id).exists())

    def test_manager_cannot_delete_own_company(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("delete_company", args=[self.service_company.id]),
        )

        self.assertRedirects(response, reverse("companys"))
        self.assertTrue(Companys.objects.filter(pk=self.service_company.id).exists())
        self.assertTrue(User.objects.filter(pk=self.manager.id).exists())

    def test_manager_can_reset_own_admin_password_without_logout(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse("reset_company_admin_password", args=[self.service_company.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        credentials = response.context["reset_credentials"]
        self.manager.refresh_from_db()
        self.assertTrue(self.manager.check_password(credentials["password"]))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.manager.id)

    def test_other_user_cannot_manage_companies(self):
        outsider = User.objects.create_user(
            username="Не служебный пользователь",
            email="outsider@example.com",
            password="outsider-pass-123",
            status="Администратор",
            companys=self.target_company,
        )
        self.client.force_login(outsider)

        list_response = self.client.get(reverse("companys"))
        reset_response = self.client.post(
            reverse("reset_company_admin_password", args=[self.target_company.id]),
        )
        delete_response = self.client.post(
            reverse("delete_company", args=[self.target_company.id]),
        )

        self.assertEqual(list_response.status_code, 403)
        self.assertEqual(reset_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)
        self.assertTrue(Companys.objects.filter(pk=self.target_company.id).exists())
