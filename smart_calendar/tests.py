from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from company.models import Companys
from felial.models import Felial
from leads.models import Record

from .models import Booking, CallBooking


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
        self.director_kc = User.objects.create_user(
            username="director_kc",
            password="test-pass-123",
            status="Директор КЦ",
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

    def test_lawyer_can_create_office_booking_without_lawyer_field(self):
        self.client.force_login(self.lawyer_1)
        response = self.client.post(
            reverse("add_office_booking", args=[self.record.id]),
            data={"date": "2026-03-16", "time": "10:15"},
        )
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.get(client=self.record)
        self.assertIsNone(booking.employees_id)

    def test_operator_can_create_office_booking_without_lawyer(self):
        self.client.force_login(self.operator)
        response = self.client.post(
            reverse("add_office_booking", args=[self.record.id]),
            data={"date": "2026-03-16", "time": "10:30"},
        )
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.get(client=self.record)
        self.assertIsNone(booking.employees_id)
        self.assertEqual(booking.registrar_id, self.operator.id)

    def test_director_kc_can_create_office_booking_without_lawyer(self):
        self.client.force_login(self.director_kc)
        response = self.client.post(
            reverse("add_office_booking", args=[self.record.id]),
            data={"date": "2026-03-16", "time": "10:45"},
        )
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.get(client=self.record)
        self.assertIsNone(booking.employees_id)
        self.assertEqual(booking.registrar_id, self.director_kc.id)

    def test_unassigned_office_booking_is_shown_in_unassigned_list(self):
        booking = Booking.objects.create(
            client=self.record,
            date="2026-03-16",
            time="10:30",
            companys=self.company,
            felial=self.felial,
            registrar=self.operator,
        )
        self.client.force_login(self.manager)
        response = self.client.get(reverse("calendar"), {"date": "2026-03-16"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(booking, list(response.context["bookings"]))
        self.assertIn(booking, list(response.context["unassigned_bookings"]))

    def test_unassigned_office_booking_is_counted_in_mini_calendar(self):
        Booking.objects.create(
            client=self.record,
            date="2026-03-16",
            time="10:30",
            companys=self.company,
            felial=self.felial,
            registrar=self.operator,
        )
        self.client.force_login(self.manager)
        response = self.client.post(reverse("get_time"), {"date": "2026-03-16"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "count-bookings")
        self.assertContains(response, 'title="Записано">1</span>')

    def test_assign_lawyer_attaches_existing_office_booking_to_lawyer(self):
        booking = Booking.objects.create(
            client=self.record,
            date="2026-03-16",
            time="10:30",
            companys=self.company,
            felial=self.felial,
            registrar=self.operator,
        )
        self.client.force_login(self.director_upp)
        response = self.client.post(
            reverse("record", args=[self.record.id]),
            data={"employees_UPP": str(self.lawyer_1.id)},
        )
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.employees_id, self.lawyer_1.id)

    def test_lawyer_calendar_shows_only_self_column(self):
        self.client.force_login(self.lawyer_1)
        response = self.client.get(reverse("calendar"))
        self.assertEqual(response.status_code, 200)
        lawyers = list(response.context["lawyers"])
        self.assertEqual(len(lawyers), 1)
        self.assertEqual(lawyers[0].id, self.lawyer_1.id)

    def test_director_kc_calendar_shows_office_booking_list(self):
        Booking.objects.create(
            client=self.record,
            date="2026-03-16",
            time="11:15",
            companys=self.company,
            felial=self.felial,
            registrar=self.operator,
        )
        self.client.force_login(self.director_kc)

        response = self.client.get(reverse("calendar"), {"date": "2026-03-16"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["use_office_booking_list"])
        self.assertContains(response, "Lead 1")
        self.assertContains(response, "11:15")

    def test_operator_calendar_shows_only_own_office_booking_list(self):
        own_record = self.record
        own_record.employees_KC = self.operator.username
        own_record.save(update_fields=["employees_KC"])
        other_record = Record.objects.create(
            name="Other Client",
            phone="+70000000002",
            description="other",
            companys=self.company,
            felial=self.felial,
            status="Новая",
            employees_KC="someone_else",
        )
        Booking.objects.create(
            client=own_record,
            date="2026-03-16",
            time="10:00",
            companys=self.company,
            felial=self.felial,
            registrar=self.operator,
        )
        Booking.objects.create(
            client=other_record,
            date="2026-03-16",
            time="12:00",
            companys=self.company,
            felial=self.felial,
            registrar=self.manager,
        )
        self.client.force_login(self.operator)

        response = self.client.get(reverse("calendar"), {"date": "2026-03-16"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["use_office_booking_list"])
        self.assertContains(response, "Lead 1")
        self.assertNotContains(response, "Other Client")
