from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from contract.models import Contract
from felial.models import Felial
from leads.models import Record

from .models import Surcharge


class SalaryCalculationTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Компания")
        self.other_company = Companys.objects.create(title="Другая компания")
        self.branch = Felial.objects.create(title="Главный", cites="Москва", companys=self.company)
        self.other_branch = Felial.objects.create(title="Главный", cites="Тула", companys=self.other_company)
        self.admin = User.objects.create_user(
            username="salary_admin", password="password", status="Администратор",
            companys=self.company, felial=self.branch,
        )
        self.manager = User.objects.create_user(
            username="salary_manager", password="password", status="Менеджер",
            companys=self.company, felial=self.branch,
        )
        self.lawyer = User.objects.create_user(
            username="salary_lawyer", password="password", status="Юрист пирвичник",
            type_zp="Процент", percent=Decimal("0.500"), bet=0,
            companys=self.company, felial=self.branch,
        )
        self.operator = User.objects.create_user(
            username="salary_operator", password="password", status="Оператор",
            type_zp="Ставка", bet=Decimal("30000"),
            companys=self.company, felial=self.branch,
        )
        self.primary_employee = User.objects.create_user(
            username="primary_employee", password="password", status="ОП",
            type_zp="Процент", percent=Decimal("0.100"), bet=0,
            companys=self.company, felial=self.branch,
        )
        self.documents_record = Record.objects.create(
            name="Документы", employees_UPP=self.lawyer.username, lawyer=self.lawyer,
            representative=False, companys=self.company, felial=self.branch,
        )
        self.representation_record = Record.objects.create(
            name="Представительство", employees_UPP=self.lawyer.username, lawyer=self.lawyer,
            representative=True, companys=self.company, felial=self.branch,
        )
        self.documents_contract = Contract.objects.create(
            record=self.documents_record, number="1001", amount=Decimal("100000"),
            initial_payment=Decimal("50000"), contract_date=date(2026, 10, 15),
        )
        self.representation_contract = Contract.objects.create(
            record=self.representation_record, number="1002", amount=Decimal("100000"),
            initial_payment=Decimal("40000"), contract_date=date(2026, 10, 16),
        )
        self.primary_record = Record.objects.create(
            name="Клиент первичника", employees_UPP=self.primary_employee.username,
            lawyer=self.primary_employee, representative=True,
            companys=self.company, felial=self.branch,
        )
        self.primary_contract = Contract.objects.create(
            record=self.primary_record, number="2001", amount=Decimal("120000"),
            initial_payment=Decimal("20000"), contract_date=date(2026, 10, 20),
        )
        Surcharge.objects.create(
            contract=self.documents_contract, cost=Decimal("10000"),
            dat=datetime(2026, 10, 10, 12), is_paid=True,
            paid_at=datetime(2026, 10, 31, 10),
        )
        Surcharge.objects.create(
            contract=self.representation_contract, cost=Decimal("5000"),
            dat=datetime(2026, 10, 20, 12), is_paid=False,
        )
        Surcharge.objects.create(
            contract=self.primary_contract, cost=Decimal("10000"),
            dat=datetime(2026, 10, 24, 12), is_paid=True,
            paid_at=datetime(2026, 10, 25, 10),
        )
        self.client.force_login(self.admin)

    def test_not_transferred_lead_is_excluded_from_salary(self):
        response = self.client.get(
            reverse("user_inform", args=[self.lawyer.id]),
            {"month": "2026-10", "period": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["documents_total"], Decimal("0"))
        self.assertEqual(response.context["representation_total"], Decimal("0"))
        self.assertEqual(response.context["zp"], Decimal("0.00"))

    def test_second_period_includes_day_16_through_month_end_and_splits_rates(self):
        response = self.client.get(
            reverse("user_inform", args=[self.lawyer.id]),
            {"month": "2026-10", "period": "2"},
        )
        self.assertEqual(response.context["documents_total"], Decimal("0"))
        self.assertEqual(response.context["representation_total"], Decimal("40000"))
        self.assertEqual(response.context["documents_salary"], Decimal("0.00"))
        self.assertEqual(response.context["representation_salary"], Decimal("3600.00"))
        self.assertEqual(response.context["zp"], Decimal("3600.00"))

    def test_unpaid_surcharge_is_not_included(self):
        response = self.client.get(
            reverse("user_inform", args=[self.lawyer.id]),
            {"month": "2026-10", "period": "2"},
        )
        self.assertEqual(response.context["surcharge_payments"], Decimal("0"))
        self.assertEqual(response.context["surcharges_count"], 0)

    def test_salary_list_contains_rate_and_percentage_employees(self):
        response = self.client.get(reverse("salary_list"), {"month": "2026-10", "period": "2"})
        self.assertEqual(response.status_code, 200)
        rows = {row["employee"].id: row for row in response.context["salary_rows"]}
        self.assertEqual(rows[self.lawyer.id]["calculation_amount"], Decimal("40000"))
        self.assertEqual(rows[self.operator.id]["calculation_amount"], Decimal("30000"))
        self.assertEqual(rows[self.operator.id]["salary"], Decimal("30000"))
        self.assertEqual(rows[self.primary_employee.id]["calculation_amount"], Decimal("30000"))
        self.assertEqual(rows[self.primary_employee.id]["salary"], Decimal("6000.00"))

    def test_primary_employee_receives_twenty_percent_of_received_money(self):
        not_transferred = Record.objects.create(
            name="Не передан", employees_UPP=self.primary_employee.username,
            lawyer=self.primary_employee, representative=False,
            companys=self.company, felial=self.branch,
        )
        Contract.objects.create(
            record=not_transferred, number="2002", amount=Decimal("50000"),
            initial_payment=Decimal("50000"), contract_date=date(2026, 10, 22),
        )
        response = self.client.get(
            reverse("user_inform", args=[self.primary_employee.id]),
            {"month": "2026-10", "period": "2"},
        )
        self.assertEqual(response.context["base_total"], Decimal("30000"))
        self.assertEqual(response.context["zp"], Decimal("6000.00"))
        self.assertEqual(len(response.context["payment_rows"]), 2)
        self.assertEqual(response.context["payment_rows"][0]["salary"], Decimal("4000.00"))
        self.assertEqual(response.context["payment_rows"][1]["salary"], Decimal("2000.00"))

    def test_manager_can_open_salary_list(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("salary_list")).status_code, 200)

    def test_employee_cannot_open_salary_section(self):
        self.client.force_login(self.lawyer)
        response = self.client.get(reverse("salary_list"))
        self.assertRedirects(response, reverse("all_leads"))

    def test_salary_page_does_not_open_employee_from_another_company(self):
        other_employee = User.objects.create_user(
            username="other_employee", password="password", status="Оператор",
            type_zp="Ставка", bet=50000, companys=self.other_company, felial=self.other_branch,
        )
        response = self.client.get(reverse("user_inform", args=[other_employee.id]))
        self.assertEqual(response.status_code, 404)

    def test_excel_contains_only_primary_lawyers_and_blank_manual_fields(self):
        response = self.client.get(
            reverse("salary_export"), {"month": "2026-10", "period": "2"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        with ZipFile(BytesIO(response.content)) as archive:
            sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn("salary_lawyer", sheet)
        self.assertIn("primary_employee", sheet)
        self.assertNotIn("salary_operator", sheet)
        self.assertIn('<c r="B4" s="4"/>', sheet)
        self.assertIn('<c r="H4" s="5"/>', sheet)
        self.assertIn('<c r="J4" s="7"/>', sheet)
        self.assertIn("E4+G4+H4", sheet)
        self.assertIn("Ведомость за период", sheet)
        self.assertIn("Сотрудники-первичники", sheet)
