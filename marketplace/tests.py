from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.models import Record
from wallet.models import CompanyWallet, WalletTransaction

from .models import LeadPurchase, LeadStreamSettings, MarketplaceLead
from .excel import build_excel_template_bytes
from .services import distribute_marketplace_leads


class MarketplaceDistributionTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Покупатель")
        self.branch = Felial.objects.create(title="Главный", cites="Москва", companys=self.company)
        self.wallet = CompanyWallet.objects.create(company=self.company, balance=Decimal("1000.00"))
        self.settings = LeadStreamSettings.objects.create(
            company=self.company,
            budget=Decimal("1000.00"),
            lead_price=Decimal("300.00"),
            is_enabled=True,
        )
        self.lead_1 = MarketplaceLead.objects.create(
            name="Иван",
            phone="+79990000001",
            note="Нужна консультация",
            city="Москва",
            topic="Банкротство",
        )
        self.lead_2 = MarketplaceLead.objects.create(
            name="Анна",
            phone="+79990000002",
            city="Москва",
            topic="Семейное право",
        )

    def test_distribution_moves_leads_to_crm_and_charges_wallet(self):
        purchases, operation = distribute_marketplace_leads(
            [self.lead_1.id, self.lead_2.id],
            self.company,
        )

        self.wallet.refresh_from_db()
        self.settings.refresh_from_db()
        self.lead_1.refresh_from_db()
        self.lead_2.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("400.00"))
        self.assertEqual(self.settings.spent_amount, Decimal("600.00"))
        self.assertEqual(operation.operation_type, WalletTransaction.TYPE_WITHDRAWAL)
        self.assertEqual(operation.amount, Decimal("600.00"))
        self.assertEqual(len(purchases), 2)
        self.assertEqual(LeadPurchase.objects.count(), 2)
        self.assertEqual(Record.objects.filter(companys=self.company, where="Биржа заявок").count(), 2)
        self.assertEqual(self.lead_1.status, MarketplaceLead.STATUS_SOLD)
        self.assertEqual(self.lead_2.buyer, self.company)
        self.assertFalse(hasattr(operation, "user"))

    def test_insufficient_wallet_rolls_back_everything(self):
        self.wallet.balance = Decimal("100.00")
        self.wallet.save(update_fields=("balance",))

        with self.assertRaises(ValidationError):
            distribute_marketplace_leads([self.lead_1.id], self.company)

        self.lead_1.refresh_from_db()
        self.settings.refresh_from_db()
        self.assertEqual(self.lead_1.status, MarketplaceLead.STATUS_AVAILABLE)
        self.assertEqual(self.settings.spent_amount, Decimal("0.00"))
        self.assertFalse(LeadPurchase.objects.exists())
        self.assertFalse(Record.objects.filter(where="Биржа заявок").exists())

    def test_insufficient_stream_budget_rolls_back_everything(self):
        self.settings.budget = Decimal("200.00")
        self.settings.save(update_fields=("budget",))

        with self.assertRaisesMessage(ValidationError, "недостаточно доступного бюджета"):
            distribute_marketplace_leads([self.lead_1.id], self.company)

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("1000.00"))
        self.assertFalse(LeadPurchase.objects.exists())

    def test_sold_lead_cannot_be_distributed_twice(self):
        distribute_marketplace_leads([self.lead_1.id], self.company)

        with self.assertRaisesMessage(ValidationError, "уже распределены"):
            distribute_marketplace_leads([self.lead_1.id], self.company)


class MarketplacePermissionsTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Компания")
        self.user = User.objects.create_user(
            username="regular_marketplace_user",
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

    def test_distribution_is_forbidden_for_regular_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("marketplace_distribution"))
        self.assertEqual(response.status_code, 403)

    def test_yrik_can_open_distribution(self):
        self.client.force_login(self.yrik)
        response = self.client.get(reverse("marketplace_distribution"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Распределение заявок")

    def test_excel_import_is_forbidden_for_regular_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("marketplace_excel_import"))
        self.assertEqual(response.status_code, 403)

    def test_yrik_can_download_marketplace_excel_template(self):
        self.client.force_login(self.yrik)
        response = self.client.get(reverse("marketplace_excel_template"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(response.content.startswith(b"PK"))

    def test_yrik_can_import_marketplace_leads_from_excel(self):
        self.client.force_login(self.yrik)
        excel_file = BytesIO(build_excel_template_bytes())
        excel_file.name = "marketplace.xlsx"
        with ZipFile(excel_file, "a") as archive:
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                (
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                    '<sheetData>'
                    '<row r="1">'
                    '<c r="A1" t="inlineStr"><is><t>Имя</t></is></c>'
                    '<c r="B1" t="inlineStr"><is><t>Телефон</t></is></c>'
                    '</row>'
                    '<row r="2">'
                    '<c r="A2" t="inlineStr"><is><t>Иван</t></is></c>'
                    '<c r="B2" t="inlineStr"><is><t>+79990000001</t></is></c>'
                    '</row>'
                    '<row r="3">'
                    '<c r="A3" t="inlineStr"><is><t>Анна</t></is></c>'
                    '<c r="B3" t="inlineStr"><is><t>+79990000002</t></is></c>'
                    '</row>'
                    '</sheetData>'
                    '</worksheet>'
                ),
            )
        excel_file.seek(0)

        response = self.client.post(reverse("marketplace_excel_import"), data={"file": excel_file})

        self.assertRedirects(response, reverse("marketplace_distribution"))
        self.assertEqual(MarketplaceLead.objects.count(), 2)
        self.assertEqual(
            list(MarketplaceLead.objects.order_by("phone").values_list("name", "status")),
            [("Иван", MarketplaceLead.STATUS_AVAILABLE), ("Анна", MarketplaceLead.STATUS_AVAILABLE)],
        )
