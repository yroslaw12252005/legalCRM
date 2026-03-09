from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.models import Record

from .models import CallBooking


class CallBookingTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Company")
        self.felial = Felial.objects.create(title="Main", cites="Moscow", companys=self.company)

        self.director_upp = User.objects.create_user(
            username="director_upp",
            password="test-pass-123",
            status="Директор ЮПП",
            companys=self.company,
            felial=self.felial,
        )
        self.lawyer_1 = User.objects.create_user(
            username="lawyer_1",
            password="test-pass-123",
            status="Юрист пирвичник",
            companys=self.company,
            felial=self.felial,
        )
        self.lawyer_2 = User.objects.create_user(
            username="lawyer_2",
            password="test-pass-123",
            status="Юрист пирвичник",
            companys=self.company,
            felial=self.felial,
        )
        self.operator = User.objects.create_user(
            username="operator_1",
            password="test-pass-123",
            status="Оператор",
            companys=self.company,
            felial=self.felial,
        )
        self.manager = User.objects.create_user(
            username="manager_1",
            password="test-pass-123",
            status="Менеджер",
            companys=self.company,
            felial=self.felial,
        )

        self.record = Record.objects.create(
            name="Lead 1",
            phone="+70000000001",
            description="test",
            companys=self.company,
            felial=self.felial,
        )

    def test_lawyer_can_create_call_for_self(self):
        self.client.force_login(self.lawyer_1)
        response = self.client.post(
            reverse("add_call_event", args=[self.record.id]),
            data={"date": "2026-03-15", "time": "10:00"},
        )
        self.assertEqual(response.status_code, 302)
        call_booking = CallBooking.objects.get(client=self.record)
        self.assertEqual(call_booking.employees_id, self.lawyer_1.id)
        self.assertEqual(call_booking.registrar_id, self.lawyer_1.id)

    def test_director_upp_can_choose_lawyer(self):
        self.client.force_login(self.director_upp)
        response = self.client.post(
            reverse("add_call_event", args=[self.record.id]),
            data={"date": "2026-03-15", "time": "11:00", "employees": str(self.lawyer_2.id)},
        )
        self.assertEqual(response.status_code, 302)
        call_booking = CallBooking.objects.get(client=self.record)
        self.assertEqual(call_booking.employees_id, self.lawyer_2.id)
        self.assertEqual(call_booking.registrar_id, self.director_upp.id)

    def test_non_allowed_role_cannot_create_call(self):
        self.client.force_login(self.operator)
        response = self.client.post(
            reverse("add_call_event", args=[self.record.id]),
            data={"date": "2026-03-15", "time": "12:00"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CallBooking.objects.filter(client=self.record).exists())

    def test_lawyer_can_create_office_booking_for_self(self):
        self.client.force_login(self.lawyer_1)
        response = self.client.post(
            reverse("add_office_booking", args=[self.record.id]),
            data={"date": "2026-03-16", "time": "10:15"},
        )
        self.assertEqual(response.status_code, 302)

    def test_manager_must_choose_lawyer_for_office_booking(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("add_office_booking", args=[self.record.id]),
            data={"date": "2026-03-16", "time": "10:30"},
        )
        self.assertEqual(response.status_code, 200)

    def test_lawyer_calendar_shows_only_self_column(self):
        self.client.force_login(self.lawyer_1)
        response = self.client.get(reverse("calendar"))
        self.assertEqual(response.status_code, 200)
        lawyers = list(response.context["lawyers"])
        self.assertEqual(len(lawyers), 1)
        self.assertEqual(lawyers[0].id, self.lawyer_1.id)
