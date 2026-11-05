from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from company.models import Companys
from contract.models import Contract
from felial.models import Felial
from smart_calendar.models import Booking

from .models import Record, RecordDocument


class RecordActivityTests(TestCase):
    def setUp(self):
        self.company = Companys.objects.create(title="Activity company")
        self.branch = Felial.objects.create(title="Main", cites="Moscow", companys=self.company)
        self.record = Record.objects.create(
            name="Client",
            phone="+79990000000",
            companys=self.company,
            felial=self.branch,
        )

    def set_record_old_without_activity_tracking(self, record=None):
        record = record or self.record
        old_time = timezone.now() - timedelta(days=2)
        Record.objects.filter(pk=record.pk).update(updated_at=old_time)
        record.refresh_from_db()
        return old_time

    def test_created_record_starts_with_creation_as_last_change(self):
        self.assertLess(abs((self.record.updated_at - self.record.created_at).total_seconds()), 2)

    def test_save_with_update_fields_also_updates_last_change(self):
        old_time = self.set_record_old_without_activity_tracking()
        self.record.status = "В работе"
        self.record.save(update_fields=["status"])
        self.record.refresh_from_db()
        self.assertGreater(self.record.updated_at, old_time)

    def test_default_ordering_uses_last_change(self):
        second = Record.objects.create(
            name="Second",
            phone="+79990000001",
            companys=self.company,
            felial=self.branch,
        )
        self.set_record_old_without_activity_tracking(second)
        ids = list(Record.objects.values_list("id", flat=True))
        self.assertEqual(ids[0], self.record.id)
        self.assertEqual(ids[1], second.id)

    def test_document_change_touches_record(self):
        old_time = self.set_record_old_without_activity_tracking()
        RecordDocument.objects.create(
            record=self.record,
            file_name="document.pdf",
            file_url="https://example.com/document.pdf",
        )
        self.record.refresh_from_db()
        self.assertGreater(self.record.updated_at, old_time)

    def test_contract_change_touches_record(self):
        old_time = self.set_record_old_without_activity_tracking()
        Contract.objects.create(
            number="101",
            amount="100000.00",
            initial_payment="10000.00",
            contract_date=timezone.now().date(),
            record=self.record,
        )
        self.record.refresh_from_db()
        self.assertGreater(self.record.updated_at, old_time)

    def test_calendar_change_touches_record(self):
        old_time = self.set_record_old_without_activity_tracking()
        Booking.objects.create(
            client=self.record,
            date=timezone.now().date(),
            time="10:00",
            companys=self.company,
            felial=self.branch,
        )
        self.record.refresh_from_db()
        self.assertGreater(self.record.updated_at, old_time)

    def test_queryset_update_tracks_bulk_actions(self):
        old_time = self.set_record_old_without_activity_tracking()
        Record.objects.filter(pk=self.record.pk).update(status="В работе")
        self.record.refresh_from_db()
        self.assertGreater(self.record.updated_at, old_time)
