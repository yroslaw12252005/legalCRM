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
        self.second_branch = Felial.objects.create(title="Второй", cites="Тула", companys=self.company)
        self.other_branch = Felial.objects.create(title="Главный", cites="Казань", companys=self.other_company)
        self.admin = User.objects.create_user(
            username="salary_admin", password="password", status="Администратор",
            companys=self.company, felial=self.branch,
        )
        self.manager = User.objects.create_user(
            username="salary_manager", password="password", status="Менеджер",
            type_zp=User.SALARY_COMBINED, percent=Decimal("10"), bet=Decimal("60000"),
            companys=self.company, felial=self.branch,
        )
        self.director = User.objects.create_user(
            username="salary_director", password="password", status="Директор ЮПП",
            type_zp=User.SALARY_FIXED, bet=Decimal("100000"),
            companys=self.company, felial=self.branch,
        )
        self.lawyer = User.objects.create_user(
            username="salary_lawyer", password="password", status="Юрист пирвичник",
            type_zp=User.SALARY_PERCENT, percent=Decimal("9"),
            companys=self.company, felial=self.branch,
        )
        self.operator = User.objects.create_user(
            username="salary_operator", password="password", status="Оператор",
            type_zp=User.SALARY_FIXED, bet=Decimal("30000"),
            companys=self.company, felial=self.branch,
        )
        self.representative = User.objects.create_user(
            username="representative_employee", password="password", status="Представитель",
            type_zp=User.SALARY_PERCENT, percent=Decimal("20"),
            companys=self.company, felial=self.branch,
        )

        self.not_transferred_record = Record.objects.create(
            name="Не передана", employees_UPP=self.lawyer.username, lawyer=self.lawyer,
            representative=False, companys=self.company, felial=self.branch,
        )
        self.transferred_record = Record.objects.create(
            name="Передана", employees_UPP=self.lawyer.username, lawyer=self.lawyer,
            representative=True, companys=self.company, felial=self.branch,
        )
        self.representative_record = Record.objects.create(
            name="Клиент представителя", employees_REP=self.representative.username,
            representative_user=self.representative,
            representative=True, companys=self.company, felial=self.branch,
        )
        self.not_transferred_contract = Contract.objects.create(
            record=self.not_transferred_record, number="1001", amount=Decimal("100000"),
            initial_payment=Decimal("50000"), contract_date=date(2026, 10, 15),
        )
        self.transferred_contract = Contract.objects.create(
            record=self.transferred_record, number="1002", amount=Decimal("100000"),
            initial_payment=Decimal("40000"), contract_date=date(2026, 10, 16),
        )
        self.representative_contract = Contract.objects.create(
            record=self.representative_record, number="2001", amount=Decimal("120000"),
            initial_payment=Decimal("20000"), contract_date=date(2026, 10, 20),
        )
        Surcharge.objects.create(
            contract=self.not_transferred_contract, cost=Decimal("10000"),
            dat=datetime(2026, 10, 10, 12), is_paid=True,
            paid_at=datetime(2026, 10, 31, 10),
        )
        Surcharge.objects.create(
            contract=self.transferred_contract, cost=Decimal("5000"),
            dat=datetime(2026, 10, 20, 12), is_paid=False,
        )
        Surcharge.objects.create(
            contract=self.representative_contract, cost=Decimal("10000"),
            dat=datetime(2026, 10, 24, 12), is_paid=True,
            paid_at=datetime(2026, 10, 25, 10),
        )
        self.client.force_login(self.admin)

    def test_not_transferred_lead_is_excluded(self):
        response = self.client.get(
            reverse("user_inform", args=[self.lawyer.id]),
            {"month": "2026-10", "period": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["base_total"], Decimal("0"))
        self.assertEqual(response.context["zp"], Decimal("0.00"))

    def test_lawyer_uses_percent_from_employee_settings(self):
        response = self.client.get(
            reverse("user_inform", args=[self.lawyer.id]),
            {"month": "2026-10", "period": "2"},
        )
        self.assertEqual(response.context["base_total"], Decimal("40000"))
        self.assertEqual(response.context["percent_value"], Decimal("9"))
        self.assertEqual(response.context["percent_salary"], Decimal("3600"))
        self.assertEqual(response.context["zp"], Decimal("3600"))

    def test_representative_uses_received_money_and_employee_percent(self):
        response = self.client.get(
            reverse("user_inform", args=[self.representative.id]),
            {"month": "2026-10", "period": "2"},
        )
        self.assertEqual(response.context["base_total"], Decimal("30000"))
        self.assertEqual(response.context["zp"], Decimal("6000"))
        self.assertEqual(len(response.context["payment_rows"]), 2)
        self.assertEqual(response.context["payment_rows"][0]["rate"], Decimal("20"))

    def test_monthly_salary_is_divided_between_two_periods(self):
        response = self.client.get(
            reverse("user_inform", args=[self.operator.id]),
            {"month": "2026-10", "period": "2"},
        )
        self.assertEqual(response.context["period_fixed_salary"], Decimal("15000"))
        self.assertEqual(response.context["calculation_amount"], Decimal("15000"))
        self.assertEqual(response.context["zp"], Decimal("15000"))

    def test_manager_combines_half_salary_and_branch_receipts_percent(self):
        response = self.client.get(
            reverse("user_inform", args=[self.manager.id]),
            {"month": "2026-10", "period": "2"},
        )
        self.assertEqual(response.context["base_total"], Decimal("70000"))
        self.assertEqual(response.context["period_fixed_salary"], Decimal("30000"))
        self.assertEqual(response.context["percent_salary"], Decimal("7000"))
        self.assertEqual(response.context["zp"], Decimal("37000"))

    def test_manager_does_not_receive_other_branch_payments(self):
        other_branch_record = Record.objects.create(
            name="Другой филиал", representative=True,
            companys=self.company, felial=self.second_branch,
        )
        Contract.objects.create(
            record=other_branch_record, number="3001", amount=Decimal("100000"),
            initial_payment=Decimal("100000"), contract_date=date(2026, 10, 20),
        )
        response = self.client.get(
            reverse("user_inform", args=[self.manager.id]),
            {"month": "2026-10", "period": "2"},
        )
        self.assertEqual(response.context["base_total"], Decimal("70000"))

    def test_director_salary_is_displayed(self):
        response = self.client.get(
            reverse("user_inform", args=[self.director.id]),
            {"month": "2026-10", "period": "2"},
        )
        self.assertEqual(response.context["calculation_amount"], Decimal("50000"))
        self.assertEqual(response.context["zp"], Decimal("50000"))

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
            type_zp=User.SALARY_FIXED, bet=50000,
            companys=self.other_company, felial=self.other_branch,
        )
        response = self.client.get(reverse("user_inform", args=[other_employee.id]))
        self.assertEqual(response.status_code, 404)

    def test_excel_contains_manager_director_lawyer_and_representative(self):
        response = self.client.get(
            reverse("salary_export"), {"month": "2026-10", "period": "2"}
        )
        self.assertEqual(response.status_code, 200)
        with ZipFile(BytesIO(response.content)) as archive:
            sheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertIn("salary_lawyer", sheet)
        self.assertIn("representative_employee", sheet)
        self.assertIn("salary_manager", sheet)
        self.assertIn("salary_director", sheet)
        self.assertNotIn("salary_operator", sheet)
        self.assertIn("Расчётная сумма", sheet)
        self.assertIn("Оклад за период", sheet)
        self.assertIn("Начислено по проценту", sheet)
        self.assertIn('<c r="B4" s="4"/>', sheet)
        self.assertIn('<c r="H4" s="5"/>', sheet)
        self.assertIn('<c r="J4" s="7"/>', sheet)
        self.assertIn("E4+G4+H4", sheet)
