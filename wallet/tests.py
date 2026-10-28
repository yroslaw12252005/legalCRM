from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys

from .models import CompanyWallet, WalletTransaction
from .services import deposit, withdraw


class WalletServiceTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Компания")
        self.wallet = CompanyWallet.objects.create(company=self.company)

    def test_deposit_updates_balance_and_creates_operation(self):
        operation = deposit(self.wallet, Decimal("1500.50"), "Оплата по счёту")

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("1500.50"))
        self.assertEqual(operation.operation_type, WalletTransaction.TYPE_DEPOSIT)
        self.assertEqual(operation.balance_after, Decimal("1500.50"))
        self.assertEqual(operation.comment, "Оплата по счёту")

    def test_withdraw_updates_balance_and_creates_operation(self):
        deposit(self.wallet, Decimal("1000.00"))
        operation = withdraw(self.wallet, Decimal("350.00"), "Покупка заявок")

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("650.00"))
        self.assertEqual(operation.operation_type, WalletTransaction.TYPE_WITHDRAWAL)
        self.assertEqual(operation.balance_after, Decimal("650.00"))

    def test_withdraw_cannot_make_balance_negative(self):
        with self.assertRaises(ValidationError):
            withdraw(self.wallet, Decimal("1.00"))

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("0.00"))
        self.assertFalse(self.wallet.transactions.exists())


class WalletViewsTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Компания клиента")
        self.other_company = Companys.objects.create(title="Другая компания")
        self.user = User.objects.create_user(
            username="regular_wallet_user",
            password="password",
            status="Администратор",
            companys=self.company,
        )
        self.yrik = User.objects.create_user(
            username="Yrik",
            password="password",
            status="Администратор",
            companys=self.company,
        )

    def test_wallet_page_shows_only_current_company_operations(self):
        wallet = CompanyWallet.objects.create(company=self.company)
        other_wallet = CompanyWallet.objects.create(company=self.other_company)
        deposit(wallet, Decimal("500.00"), "Наша операция")
        deposit(other_wallet, Decimal("900.00"), "Чужая операция")
        self.client.force_login(self.user)

        response = self.client.get(reverse("wallet_detail"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["wallet"].balance, Decimal("500.00"))
        self.assertContains(response, "Наша операция")
        self.assertNotContains(response, "Чужая операция")
        self.assertNotContains(response, "Валидация платежа")

    def test_validation_page_is_forbidden_for_regular_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("wallet_validate_payment"))

        self.assertEqual(response.status_code, 403)

    def test_yrik_can_validate_payment(self):
        self.client.force_login(self.yrik)

        response = self.client.post(
            reverse("wallet_validate_payment"),
            {"company": self.other_company.pk, "amount": "1250.75", "comment": "Чек получен"},
        )

        self.assertRedirects(
            response,
            reverse("wallet_validate_payment"),
            fetch_redirect_response=False,
        )
        wallet = CompanyWallet.objects.get(company=self.other_company)
        self.assertEqual(wallet.balance, Decimal("1250.75"))
        operation = wallet.transactions.get()
        self.assertEqual(operation.comment, "Чек получен")
        self.assertFalse(hasattr(operation, "user"))

    def test_yrik_sees_validation_button(self):
        self.client.force_login(self.yrik)

        response = self.client.get(reverse("wallet_detail"))

        self.assertContains(response, "Валидация платежа")
