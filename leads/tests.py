from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.forms import Employees_KCForm
from leads.models import Record


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.company_1 = Companys.objects.create(title="Company 1", telegram_bot="bot-1")
        self.company_2 = Companys.objects.create(title="Company 2", telegram_bot="bot-2")

        self.felial_1 = Felial.objects.create(title="Main", cites="Moscow", companys=self.company_1)
        self.felial_2 = Felial.objects.create(title="Main", cites="SPB", companys=self.company_2)

        self.director_1 = User.objects.create_user(
            username="director_1",
            password="test-pass-123",
            status="Директор КЦ",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.operator_1 = User.objects.create_user(
            username="operator_1",
            password="test-pass-123",
            status="Оператор",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.operator_actor = User.objects.create_user(
            username="operator_actor",
            password="test-pass-123",
            status="Оператор",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.operator_2 = User.objects.create_user(
            username="operator_2",
            password="test-pass-123",
            status="Оператор",
            companys=self.company_2,
            felial=self.felial_2,
        )

        self.record_1 = Record.objects.create(
            name="Lead 1",
            phone="+70000000001",
            description="test",
            companys=self.company_1,
            felial=self.felial_1,
        )
        self.record_2 = Record.objects.create(
            name="Lead 2",
            phone="+70000000002",
            description="test",
            companys=self.company_2,
            felial=self.felial_2,
        )

    def test_employees_form_filters_by_record_company(self):
        form = Employees_KCForm(instance=self.record_1, user=self.director_1, company_id=self.record_1.companys_id)
        self.assertIn(self.operator_1, form.fields["employees_KC"].queryset)
        self.assertNotIn(self.operator_2, form.fields["employees_KC"].queryset)

    def test_record_page_denies_cross_company_access(self):
        self.client.force_login(self.director_1)
        response = self.client.get(reverse("record", args=[self.record_2.id]))
        self.assertEqual(response.status_code, 404)

    def test_record_post_rejects_employee_from_other_company(self):
        self.client.force_login(self.director_1)
        response = self.client.post(
            reverse("record", args=[self.record_1.id]),
            data={"employees_KC": str(self.operator_2.id)},
        )
        self.assertEqual(response.status_code, 200)

        self.record_1.refresh_from_db()
        self.assertNotEqual(self.record_1.employees_KC, self.operator_2.username)

    def test_record_post_accepts_employee_from_same_company(self):
        self.client.force_login(self.director_1)
        response = self.client.post(
            reverse("record", args=[self.record_1.id]),
            data={"employees_KC": str(self.operator_1.id)},
        )
        self.assertEqual(response.status_code, 200)

        self.record_1.refresh_from_db()
        self.assertEqual(self.record_1.employees_KC, self.operator_1.username)

    def test_record_post_requires_role_for_assignment(self):
        self.client.force_login(self.operator_actor)
        response = self.client.post(
            reverse("record", args=[self.record_1.id]),
            data={"employees_KC": str(self.operator_1.id)},
        )
        self.assertEqual(response.status_code, 302)

        self.record_1.refresh_from_db()
        self.assertNotEqual(self.record_1.employees_KC, self.operator_1.username)
