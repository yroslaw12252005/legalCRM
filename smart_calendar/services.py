from accounts.models import User

from .models import Booking, CallBooking


LAWYER_PRIMARY_STATUS = "Юрист пирвичник"


def _status_variants(value):
    variants = {value}
    try:
        variants.add(value.encode("utf-8").decode("cp1251"))
    except Exception:
        pass
    try:
        variants.add(value.encode("cp1251").decode("utf-8"))
    except Exception:
        pass
    return variants


def get_record_primary_lawyer(record):
    username = (record.employees_UPP or "").strip()
    if not username:
        return None

    queryset = User.objects.filter(
        username=username,
        companys_id=record.companys_id,
        status__in=list(_status_variants(LAWYER_PRIMARY_STATUS)),
    )
    if record.felial_id:
        queryset = queryset.filter(felial_id=record.felial_id)
    return queryset.first()


def office_booking_has_lawyer_conflict(booking, lawyer):
    if not lawyer or not booking.date or not booking.time:
        return False

    office_bookings = Booking.objects.filter(
        date=booking.date,
        time=booking.time,
        companys_id=booking.companys_id,
        employees=lawyer,
    )
    if booking.pk:
        office_bookings = office_bookings.exclude(pk=booking.pk)
    if booking.felial_id:
        office_bookings = office_bookings.filter(felial_id=booking.felial_id)
    if office_bookings.exists():
        return True

    call_bookings = CallBooking.objects.filter(
        date=booking.date,
        time=booking.time,
        companys_id=booking.companys_id,
        employees=lawyer,
    )
    if booking.felial_id:
        call_bookings = call_bookings.filter(felial_id=booking.felial_id)
    return call_bookings.exists()


def record_office_bookings_have_lawyer_conflict(record, lawyer):
    if not lawyer:
        return False

    bookings = Booking.objects.filter(client=record, companys_id=record.companys_id)
    for booking in bookings:
        if office_booking_has_lawyer_conflict(booking, lawyer):
            return True
    return False


def sync_record_office_bookings_to_lawyer(record, lawyer=None):
    if lawyer is None:
        lawyer = get_record_primary_lawyer(record)

    return Booking.objects.filter(
        client=record,
        companys_id=record.companys_id,
    ).update(employees=lawyer)
