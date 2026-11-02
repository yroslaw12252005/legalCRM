from django.contrib.auth import authenticate
from django.test import TestCase
from django.urls import reverse

from company.models import Companys
from felial.models import Felial
from leads.models import Record

from .models import User
from .forms import AddSuperEmployeesForm


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
