from django.contrib.auth import authenticate
from django.apps import apps as django_apps
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from importlib import import_module

from company.models import Companys
from felial.models import Felial
from leads.models import Record

from .models import User
from .forms import AddEmployeesForm, AddSuperEmployeesForm


class AdministratorOnboardingTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Обучение")
        self.branch = Felial.objects.create(
            title="Главный",
            cites="Москва",
            companys=self.company,
        )
        self.admin = User.objects.create_user(
            username="onboarding_admin",
            email="onboarding-admin@example.com",
            password="test-pass-123",
            status="Администратор",
            companys=self.company,
            felial=self.branch,
        )
        self.employee = User.objects.create_user(
            username="onboarding_employee",
            email="onboarding-employee@example.com",
            password="test-pass-123",
            status="Оператор",
            companys=self.company,
            felial=self.branch,
        )

    def test_new_admin_is_ready_for_automatic_onboarding(self):
        self.assertTrue(self.admin.should_start_onboarding)
        self.assertEqual(self.admin.onboarding_step, 0)

    def test_data_migration_does_not_autostart_for_existing_users(self):
        migration = import_module("accounts.migrations.0012_user_onboarding")

        migration.mark_existing_users_as_onboarded(django_apps, None)

        self.admin.refresh_from_db()
        self.employee.refresh_from_db()
        self.assertEqual(self.admin.onboarding_version, User.ONBOARDING_VERSION)
        self.assertEqual(self.employee.onboarding_version, User.ONBOARDING_VERSION)
        self.assertFalse(self.admin.should_start_onboarding)

    def test_admin_can_save_progress_and_complete_onboarding(self):
        self.client.force_login(self.admin)

        progress_response = self.client.post(
            reverse("update_onboarding"),
            {"action": "progress", "step": 6},
        )
        self.assertEqual(progress_response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.onboarding_step, 6)

        complete_response = self.client.post(
            reverse("update_onboarding"),
            {"action": "complete"},
        )
        self.assertEqual(complete_response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.onboarding_version, User.ONBOARDING_VERSION)
        self.assertFalse(self.admin.should_start_onboarding)
        self.assertIsNotNone(self.admin.onboarding_completed_at)

    def test_onboarding_accepts_steps_from_extended_page_tour(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("update_onboarding"),
            {"action": "progress", "step": 19},
        )

        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.onboarding_step, 19)

    def test_onboarding_clamps_unknown_step_to_supported_maximum(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("update_onboarding"),
            {"action": "progress", "step": 999},
        )

        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertEqual(
            self.admin.onboarding_step,
            User.ONBOARDING_MAX_STEP,
        )

    def test_admin_can_defer_onboarding_for_one_day(self):
        self.client.force_login(self.admin)
        before = timezone.now() + timedelta(hours=23)

        response = self.client.post(
            reverse("update_onboarding"),
            {"action": "defer"},
        )

        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertGreater(self.admin.onboarding_deferred_until, before)
        self.assertFalse(self.admin.should_start_onboarding)

    def test_restart_resets_onboarding_and_redirects_to_dashboard(self):
        self.admin.onboarding_version = User.ONBOARDING_VERSION
        self.admin.onboarding_completed_at = timezone.now()
        self.admin.save(
            update_fields=["onboarding_version", "onboarding_completed_at"]
        )
        self.client.force_login(self.admin)

        response = self.client.post(reverse("restart_onboarding"))

        self.assertRedirects(
            response,
            f"{reverse('current_applications')}?tour=1",
            fetch_redirect_response=False,
        )
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.onboarding_version, 0)
        self.assertEqual(self.admin.onboarding_step, 0)
        self.assertTrue(self.admin.should_start_onboarding)

    def test_onboarding_controls_are_admin_only(self):
        self.client.force_login(self.employee)

        update_response = self.client.post(
            reverse("update_onboarding"),
            {"action": "progress", "step": 2},
        )
        restart_response = self.client.post(reverse("restart_onboarding"))
        page_response = self.client.get(reverse("current_applications"))

        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(restart_response.status_code, 302)
        self.assertNotContains(page_response, "Пройти обучение")

    def test_admin_menu_contains_restart_button(self):
        self.admin.onboarding_version = User.ONBOARDING_VERSION
        self.admin.save(update_fields=["onboarding_version"])
        self.client.force_login(self.admin)

        response = self.client.get(reverse("current_applications"))

        self.assertContains(response, "Пройти обучение")
        self.assertContains(response, reverse("restart_onboarding"))


class EmailAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="email_user",
            email="User@Example.com",
            password="test-pass-123",
            status="Администратор",
        )

    def test_authenticates_by_email_case_insensitively(self):
        authenticated = authenticate(
            email="user@example.com",
            password="test-pass-123",
        )

        self.assertEqual(authenticated, self.user)

    def test_standard_username_argument_accepts_email_for_admin_login(self):
        authenticated = authenticate(
            username="USER@example.com",
            password="test-pass-123",
        )

        self.assertEqual(authenticated, self.user)

    def test_username_is_not_accepted_as_login_identifier(self):
        authenticated = authenticate(
            username=self.user.username,
            password="test-pass-123",
        )

        self.assertIsNone(authenticated)

    def test_duplicate_email_is_rejected_as_ambiguous(self):
        User.objects.create_user(
            username="second_email_user",
            email="user@example.com",
            password="test-pass-123",
            status="Администратор",
        )

        authenticated = authenticate(
            email="user@example.com",
            password="test-pass-123",
        )

        self.assertIsNone(authenticated)

    def test_duplicate_email_uses_password_to_select_one_account(self):
        second_user = User.objects.create_user(
            username="second_email_user",
            email="user@example.com",
            password="different-pass-456",
            status="Администратор",
        )

        authenticated = authenticate(
            email="user@example.com",
            password="different-pass-456",
        )

        self.assertEqual(authenticated, second_user)

    def test_inactive_user_cannot_authenticate(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        authenticated = authenticate(
            email="user@example.com",
            password="test-pass-123",
        )

        self.assertIsNone(authenticated)

    def test_main_login_form_accepts_email(self):
        response = self.client.post(
            reverse("all_leads"),
            {"email": "user@example.com", "password": "test-pass-123"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.id)


class UsernameValidationTests(TestCase):
    def test_registration_accepts_and_preserves_internal_space(self):
        form = AddSuperEmployeesForm(
            data={
                "username": "Иван Иванов",
                "email": "ivan@example.com",
                "password1": "safe-test-pass-123",
                "password2": "safe-test-pass-123",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.username, "Иван Иванов")


class EmployeeSalaryFormTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Компания зарплаты")
        self.branch = Felial.objects.create(
            title="Главный",
            cites="Москва",
            companys=self.company,
        )
        self.admin = User.objects.create_user(
            username="salary_form_admin",
            email="salary-form-admin@example.com",
            password="test-pass-123",
            status="Администратор",
            companys=self.company,
            felial=self.branch,
        )

    def form_data(self, **overrides):
        data = {
            "username": "Новый сотрудник",
            "email": "new-salary@example.com",
            "status": "Менеджер",
            "felial": str(self.branch.id),
            "type_zp": User.SALARY_PERCENT,
            "percent": "10",
            "bet": "",
            "password1": "safe-test-pass-123",
            "password2": "safe-test-pass-123",
        }
        data.update(overrides)
        return data

    def test_percent_salary_requires_only_percent(self):
        form = AddEmployeesForm(data=self.form_data(), user=self.admin)
        self.assertTrue(form.is_valid(), form.errors)
        employee = form.save(commit=False)
        self.assertEqual(employee.percent, 10)
        self.assertIsNone(employee.bet)

    def test_fixed_salary_requires_monthly_salary_and_clears_percent(self):
        form = AddEmployeesForm(
            data=self.form_data(type_zp=User.SALARY_FIXED, percent="25", bet="80000"),
            user=self.admin,
        )
        self.assertTrue(form.is_valid(), form.errors)
        employee = form.save(commit=False)
        self.assertIsNone(employee.percent)
        self.assertEqual(employee.bet, 80000)

    def test_combined_salary_requires_both_values(self):
        form = AddEmployeesForm(
            data=self.form_data(type_zp=User.SALARY_COMBINED, percent="", bet="80000"),
            user=self.admin,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("percent", form.errors)

    def test_salary_type_choices_match_ui(self):
        form = AddEmployeesForm(user=self.admin)
        self.assertEqual(
            list(form.fields["type_zp"].choices),
            list(User.SALARY_TYPE_CHOICES),
        )

    def test_salary_migration_preserves_old_coefficient_and_type(self):
        employee = User.objects.create_user(
            username="legacy_salary_employee",
            email="legacy-salary@example.com",
            password="test-pass-123",
            status="Менеджер",
            companys=self.company,
            felial=self.branch,
            type_zp="Процент + Ставка",
            percent="0.125",
            bet="80000",
        )
        migration = import_module("accounts.migrations.0010_salary_settings")
        migration.normalize_salary_settings(django_apps, None)
        employee.refresh_from_db()
        self.assertEqual(employee.type_zp, User.SALARY_COMBINED)
        self.assertEqual(employee.percent, 12.5)


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
        self.representative = User.objects.create_user(
            username="representative",
            password="test-pass-123",
            status="Представитель",
            companys=self.company,
            felial=self.branch,
        )
        self.record = Record.objects.create(
            name="Клиент",
            companys=self.company,
            felial=self.branch,
            lawyer=self.lawyer,
            employees_UPP=self.lawyer.username,
            representative=True,
            representative_user=self.representative,
            employees_REP=self.representative.username,
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

    def test_delete_representative_deactivates_and_preserves_assignment(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("delete_employee", args=[self.representative.id])
        )

        self.assertEqual(response.status_code, 302)
        self.representative.refresh_from_db()
        self.record.refresh_from_db()
        self.assertFalse(self.representative.is_active)
        self.assertEqual(
            self.record.representative_user_id,
            self.representative.id,
        )
        self.assertEqual(self.record.employees_REP, self.representative.username)
