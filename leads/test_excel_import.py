from io import BytesIO
from zipfile import ZipFile

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.models import Record
from leads.views import _build_excel_template_bytes


class ExcelImportTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Excel Company")
        self.felial = Felial.objects.create(title="Main", cites="Moscow", companys=self.company)
        self.admin = User.objects.create_user(
            username="excel_admin",
            password="test-pass-123",
            status="Администратор",
            companys=self.company,
            felial=self.felial,
        )
        self.operator = User.objects.create_user(
            username="excel_operator",
            password="test-pass-123",
            status="Оператор",
            companys=self.company,
            felial=self.felial,
        )

    def test_admin_can_download_excel_template(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("download_excel_template"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(response.content.startswith(b"PK"))

    def test_non_admin_cannot_open_excel_import(self):
        self.client.force_login(self.operator)

        response = self.client.get(reverse("import_records_from_excel"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("all_leads"))

    def test_admin_can_import_records_from_excel(self):
        self.client.force_login(self.admin)

        excel_file = BytesIO(_build_excel_template_bytes())
        excel_file.name = "import.xlsx"
        with ZipFile(excel_file, "a") as archive:
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                (
                    "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
                    "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
                    "<sheetData>"
                    "<row r=\"1\">"
                    "<c r=\"A1\" t=\"inlineStr\"><is><t>Имя</t></is></c>"
                    "<c r=\"B1\" t=\"inlineStr\"><is><t>Телефон</t></is></c>"
                    "</row>"
                    "<row r=\"2\">"
                    "<c r=\"A2\" t=\"inlineStr\"><is><t>Иван</t></is></c>"
                    "<c r=\"B2\" t=\"inlineStr\"><is><t>+79990000001</t></is></c>"
                    "</row>"
                    "<row r=\"3\">"
                    "<c r=\"A3\" t=\"inlineStr\"><is><t>Мария</t></is></c>"
                    "<c r=\"B3\" t=\"inlineStr\"><is><t>+79990000002</t></is></c>"
                    "</row>"
                    "</sheetData>"
                    "</worksheet>"
                ),
            )
        excel_file.seek(0)

        response = self.client.post(reverse("import_records_from_excel"), data={"file": excel_file})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("all_leads"))

        records = Record.objects.filter(companys=self.company).order_by("phone")
        self.assertEqual(records.count(), 2)
        self.assertEqual(records[0].name, "Иван")
        self.assertEqual(records[0].status, "Новая")
        self.assertEqual(records[0].where, "Exel")
        self.assertEqual(records[1].name, "Мария")
        self.assertEqual(records[1].status, "Новая")
