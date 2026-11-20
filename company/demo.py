import random
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from call_recording.models import CallRecording
from company.models import Companys
from contract.models import Contract
from cost.models import Surcharge
from felial.models import Felial
from leads.models import Record
from smart_calendar.models import Booking, CallBooking, RepresentativeBooking
from tilda_integration.models import TildaIntegration
from tilda_integration.services import hash_secret
from todolist.models import ToDoList
from wallet.models import CompanyWallet, WalletTransaction


DEMO_LIFETIME = timedelta(hours=2)
FIRST_NAMES = ("Алексей", "Марина", "Дмитрий", "Елена", "Илья", "Ольга", "Сергей", "Анна")
LAST_NAMES = ("Иванов", "Соколова", "Орлов", "Крылова", "Морозов", "Волкова")
LEAD_TYPES = (
    "Банкротство физических лиц",
    "Семейное право",
    "Кредитный спор",
    "Наследство",
    "Защита прав потребителей",
)
SOURCES = ("Tilda", "Яндекс Директ", "Рекомендация", "Входящий звонок", "Авито")
STATUSES = ("Новая", "В работе", "Записан в офис", "Заключён договор", "Передан представителю", "Отказ")


def _aware(day, hour=12, minute=0):
    value = datetime.combine(day, time(hour=hour, minute=minute))
    if settings.USE_TZ and timezone.is_naive(value):
        return timezone.make_aware(value)
    return value


def _period_start(today):
    return today.replace(day=1 if today.day <= 15 else 16)


def _employee(*, username, email, status, company, branch, salary_type=None, percent=None, bet=None):
    user = User(
        username=username,
        email=email,
        status=status,
        companys=company,
        felial=branch,
        type_zp=salary_type,
        percent=percent,
        bet=bet,
        is_active=True,
    )
    user.set_unusable_password()
    user.save()
    return user


@transaction.atomic
def create_demo_company(*, lead_count=36, lifetime=DEMO_LIFETIME):
    lead_count = max(int(lead_count), 18)
    now = timezone.now()
    today = now.date()
    session_key = uuid.uuid4()
    suffix = session_key.hex[:6]
    randomizer = random.Random(session_key.int & 0xFFFFFFFF)

    company = Companys.objects.create(
        title=f"Право Плюс · демо {suffix}",
        work_mode=Companys.MODE_TEAM,
        subscription_expires_at=today + timedelta(days=1),
        is_subscription_blocked=False,
        is_demo=True,
        demo_session_key=session_key,
        demo_expires_at=now + lifetime,
    )
    moscow = Felial.objects.create(cites="Москва", title="Главный офис", companys=company)
    petersburg = Felial.objects.create(cites="Санкт-Петербург", title="Северо-Запад", companys=company)

    admin = _employee(
        username=f"Анна Соколова · {suffix}", email=f"demo-{suffix}@example.test",
        status="Администратор", company=company, branch=moscow,
        salary_type=User.SALARY_FIXED, bet=Decimal("120000"),
    )
    operator_one = _employee(
        username=f"Мария Орлова · {suffix}", email=f"operator1-{suffix}@example.test",
        status="Оператор", company=company, branch=moscow,
        salary_type=User.SALARY_COMBINED, percent=Decimal("5"), bet=Decimal("45000"),
    )
    operator_two = _employee(
        username=f"Игорь Волков · {suffix}", email=f"operator2-{suffix}@example.test",
        status="Оператор", company=company, branch=petersburg,
        salary_type=User.SALARY_FIXED, bet=Decimal("60000"),
    )
    lawyer_one = _employee(
        username=f"Алексей Морозов · {suffix}", email=f"lawyer1-{suffix}@example.test",
        status="Юрист первичник", company=company, branch=moscow,
        salary_type=User.SALARY_PERCENT, percent=Decimal("20"),
    )
    lawyer_two = _employee(
        username=f"Елена Крылова · {suffix}", email=f"lawyer2-{suffix}@example.test",
        status="Юрист первичник", company=company, branch=petersburg,
        salary_type=User.SALARY_COMBINED, percent=Decimal("12"), bet=Decimal("70000"),
    )
    representative_one = _employee(
        username=f"Дмитрий Иванов · {suffix}", email=f"representative1-{suffix}@example.test",
        status="Представитель", company=company, branch=moscow,
        salary_type=User.SALARY_PERCENT, percent=Decimal("9"),
    )
    representative_two = _employee(
        username=f"Ольга Власова · {suffix}", email=f"representative2-{suffix}@example.test",
        status="Представитель", company=company, branch=petersburg,
        salary_type=User.SALARY_COMBINED, percent=Decimal("10"), bet=Decimal("80000"),
    )
    manager = _employee(
        username=f"Сергей Лебедев · {suffix}", email=f"manager-{suffix}@example.test",
        status="Менеджер", company=company, branch=moscow,
        salary_type=User.SALARY_FIXED, bet=Decimal("90000"),
    )

    operators = (operator_one, operator_two)
    lawyers = (lawyer_one, lawyer_two)
    representatives = (representative_one, representative_two)
    branches = (moscow, petersburg)
    records = []
    for index in range(lead_count):
        branch = branches[index % len(branches)]
        operator = operators[index % len(operators)]
        lawyer = lawyers[index % len(lawyers)]
        representative = representatives[index % len(representatives)]
        is_transferred = index < 24 or index % 4 == 0
        created = now - timedelta(days=randomizer.randint(0, 75), hours=randomizer.randint(0, 18))
        first_name = FIRST_NAMES[index % len(FIRST_NAMES)]
        last_name = LAST_NAMES[(index * 3) % len(LAST_NAMES)]
        record = Record.objects.create(
            name=f"{last_name} {first_name}",
            phone=f"+7 900 000-{index // 100:02d}-{index % 100:02d}",
            email=f"demo-client-{suffix}-{index:03d}@example.test",
            description="Демонстрационная заявка: клиенту требуется первичная консультация.",
            work_comment_kc="Контакт подтверждён, потребность уточнена.",
            work_comment="Подготовить перечень документов к встрече.",
            status=STATUSES[index % len(STATUSES)],
            type=LEAD_TYPES[index % len(LEAD_TYPES)],
            where=SOURCES[index % len(SOURCES)],
            cost=Decimal(str((60 + (index % 5) * 30) * 1000)),
            companys=company,
            felial=branch,
            employees_KC=operator.username,
            employees_UPP=lawyer.username,
            lawyer=lawyer,
            representative=is_transferred,
            representative_user=representative if is_transferred else None,
            employees_REP=representative.username if is_transferred else "Не прикреплён",
            in_work=index % 6 != 0,
            paid_online=1 if index % 11 == 0 else 0,
        )
        Record.objects.filter(pk=record.pk).update(created_at=created, updated_at=created + timedelta(days=index % 8))
        records.append(record)

    period_start = _period_start(today)
    period_length = max((today - period_start).days, 0)
    contract_records = [record for record in records if record.representative][:18]
    for index, record in enumerate(contract_records):
        contract_day = period_start + timedelta(days=index % (period_length + 1))
        amount = Decimal(str((90 + (index % 4) * 30) * 1000))
        contract = Contract.objects.create(
            number=str(700000 + index), amount=amount,
            initial_payment=Decimal("30000") + Decimal(str((index % 3) * 10000)),
            contract_date=contract_day, record=record,
        )
        if index % 2 == 0:
            paid_at = _aware(contract_day, 14, 30)
            Surcharge.objects.create(
                cost=Decimal("15000") + Decimal(str((index % 3) * 5000)),
                dat=paid_at, contract=contract, responsible=record.lawyer,
                is_paid=True, paid_at=paid_at, paid_by=admin,
            )

    for index, record in enumerate(records[:10]):
        Booking.objects.create(
            client=record, date=today + timedelta(days=(index % 5) - 2),
            time=f"{10 + index % 7:02d}:{'30' if index % 2 else '00'}",
            employees=record.lawyer, registrar=operators[index % 2],
            come=(True if index % 3 == 0 else None), companys=company, felial=record.felial,
        )
    for index, record in enumerate(records[10:18]):
        CallBooking.objects.create(
            client=record, date=today + timedelta(days=index % 4), time=f"{11 + index:02d}:15",
            employees=operators[index % 2], registrar=admin, companys=company, felial=record.felial,
        )
    for index, record in enumerate(contract_records[:6]):
        RepresentativeBooking.objects.create(
            destination="Арбитражный суд" if index % 2 == 0 else "Районный суд",
            client=record, date=today + timedelta(days=index + 1), time=f"{9 + index:02d}:00",
            representative=record.representative_user, registrar=admin,
            companys=company, felial=record.felial,
        )

    task_owners = (admin, operator_one, lawyer_one, representative_one, manager)
    for index in range(12):
        ToDoList.objects.create(
            title=("Связаться с клиентом" if index % 2 == 0 else "Проверить документы"),
            description="Демонстрационная задача по текущей заявке.",
            time=now + timedelta(hours=(index - 3) * 4), made=index % 5 == 0,
            priority=("Высокий" if index % 3 == 0 else "Средний"),
            category="Клиенты", user=task_owners[index % len(task_owners)].id,
        )

    wallet = CompanyWallet.objects.create(company=company, balance=Decimal("14850"))
    WalletTransaction.objects.create(
        wallet=wallet, operation_type=WalletTransaction.TYPE_DEPOSIT,
        amount=Decimal("20000"), balance_after=Decimal("20000"), comment="Демонстрационное пополнение",
    )
    WalletTransaction.objects.create(
        wallet=wallet, operation_type=WalletTransaction.TYPE_WITHDRAWAL,
        amount=Decimal("5150"), balance_after=Decimal("14850"), comment="Получение заявок на бирже",
    )

    TildaIntegration.objects.create(
        company=company, branch=moscow, title="Основной лендинг",
        secret_hash=hash_secret(uuid.uuid4().hex), is_active=False, created_by=admin,
        last_request_at=now - timedelta(hours=2), total_received=147,
        total_processed=132, total_duplicates=9, total_rejected=6,
    )
    for index in range(5):
        CallRecording.objects.create(
            companys=company, phone=records[index].phone,
            operator_phone=f"demo-{index + 1}", external_id=f"demo-{session_key}-{index}",
            file_name=f"demo-call-{index + 1}.mp3", file_url="https://example.test/demo-call.mp3",
            s3_key=f"demo/{session_key}/{index}.mp3", call_started_at=now - timedelta(hours=index + 1),
        )

    return company, admin


@transaction.atomic
def delete_demo_company(company):
    company = Companys.objects.select_for_update().filter(pk=company.pk).first()
    if company is None:
        return False
    if not company.is_demo:
        raise ValueError("Удаление разрешено только для демонстрационной компании")
    user_ids = list(User.objects.filter(companys=company).values_list("id", flat=True))
    ToDoList.objects.filter(user__in=user_ids).delete()
    TildaIntegration.objects.filter(company=company).delete()
    Record.objects.filter(companys=company).delete()
    CallRecording.objects.filter(companys=company).delete()
    User.objects.filter(companys=company).delete()
    company.delete()
    return True


def cleanup_expired_demo_companies(*, limit=25):
    ids = list(
        Companys.objects.filter(
            is_demo=True,
            demo_expires_at__lte=timezone.now(),
        ).order_by("demo_expires_at").values_list("id", flat=True)[:limit]
    )
    deleted = 0
    for company_id in ids:
        company = Companys.objects.filter(pk=company_id, is_demo=True).first()
        if company:
            delete_demo_company(company)
            deleted += 1
    return deleted
