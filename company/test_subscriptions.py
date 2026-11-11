from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from company.models import Companys
from company.subscriptions import subscription_warning_days


class CompanySubscriptionTests(TestCase):
    def setUp(self):
        self.manager_company = Companys.objects.create(title="rossCRM")
        self.manager = User.objects.create_user(
            username="Manager",
            email="yrik@gmail.com",
            password="secret123",
            status="Администратор",
            companys=self.manager_company,
        )
        self.company = Companys.objects.create(title="Тестовая компания")
        self.employee = User.objects.create_user(
            username="Employee",
            email="employee@example.com",
            password="secret123",
            status="Юрист",
            companys=self.company,
        )

    def test_manager_can_set_subscription_expiration(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("update_company_subscription", args=[self.company.pk]),
            {"subscription_expires_at": "2030-05-17"},
        )

        self.assertRedirects(response, reverse("companys"))
        self.company.refresh_from_db()
        self.assertEqual(str(self.company.subscription_expires_at), "2030-05-17")

    def test_manual_block_and_unblock_synchronizes_all_users(self):
        second_employee = User.objects.create_user(
            username="Employee 2",
            email="employee2@example.com",
            password="secret123",
            status="Менеджер",
            companys=self.company,
        )
        self.client.force_login(self.manager)

        self.client.post(reverse("block_company", args=[self.company.pk]))
        self.company.refresh_from_db()
        self.employee.refresh_from_db()
        second_employee.refresh_from_db()
        self.assertTrue(self.company.is_subscription_blocked)
        self.assertTrue(self.employee.is_account_blocked)
        self.assertTrue(second_employee.is_account_blocked)

        self.client.post(reverse("unblock_company", args=[self.company.pk]))
        self.company.refresh_from_db()
        self.employee.refresh_from_db()
        second_employee.refresh_from_db()
        self.assertFalse(self.company.is_subscription_blocked)
        self.assertFalse(self.employee.is_account_blocked)
        self.assertFalse(second_employee.is_account_blocked)

    def test_expired_subscription_blocks_company_on_next_request(self):
        self.company.subscription_expires_at = timezone.now().date() - timedelta(days=1)
        self.company.save(update_fields=["subscription_expires_at"])
        self.client.force_login(self.employee)

        response = self.client.get("/current-applications/")

        self.assertRedirects(
            response,
            reverse("account_blocked"),
            fetch_redirect_response=False,
        )
        self.company.refresh_from_db()
        self.employee.refresh_from_db()
        self.assertTrue(self.company.is_subscription_blocked)
        self.assertTrue(self.employee.is_account_blocked)

    def test_expiration_day_itself_is_still_active(self):
        self.company.subscription_expires_at = timezone.now().date()
        self.company.save(update_fields=["subscription_expires_at"])
        self.client.force_login(self.employee)

        response = self.client.get(reverse("account_blocked"))

        self.company.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.company.is_subscription_blocked)

    def test_blocked_page_has_support_email(self):
        self.company.is_subscription_blocked = True
        self.company.save(update_fields=["is_subscription_blocked"])
        self.employee.is_account_blocked = True
        self.employee.save(update_fields=["is_account_blocked"])
        self.client.force_login(self.employee)

        response = self.client.get(reverse("account_blocked"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response,
            'href="mailto:info@rossurist.ru"',
            status_code=403,
        )

    def test_only_manager_email_can_manage_subscription(self):
        self.client.force_login(self.employee)
        response = self.client.post(reverse("block_company", args=[self.company.pk]))
        self.assertEqual(response.status_code, 403)

    def test_warning_is_only_returned_three_two_or_one_days_before(self):
        today = timezone.now().date()
        for days in (3, 2, 1):
            self.company.subscription_expires_at = today + timedelta(days=days)
            self.assertEqual(subscription_warning_days(self.company, today), days)

        self.company.subscription_expires_at = today + timedelta(days=4)
        self.assertIsNone(subscription_warning_days(self.company, today))

    def test_warning_is_rendered_under_navigation(self):
        self.manager_company.subscription_expires_at = timezone.now().date() + timedelta(days=3)
        self.manager_company.save(update_fields=["subscription_expires_at"])
        self.client.force_login(self.manager)

        response = self.client.get(reverse("companys"))

        self.assertContains(response, "Подписка истечёт через 3")
        self.assertContains(response, "mailto:info@rossurist.ru")

    def test_expired_company_cannot_be_unblocked_until_date_is_extended(self):
        self.company.subscription_expires_at = timezone.now().date() - timedelta(days=1)
        self.company.is_subscription_blocked = True
        self.company.save(
            update_fields=["subscription_expires_at", "is_subscription_blocked"]
        )
        self.client.force_login(self.manager)

        self.client.post(reverse("unblock_company", args=[self.company.pk]))

        self.company.refresh_from_db()
        self.assertTrue(self.company.is_subscription_blocked)
