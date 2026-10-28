from django.db import DatabaseError

from .models import CompanyWallet


def company_wallet(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.companys_id:
        return {"sidebar_wallet": None, "can_validate_wallet_payment": False}

    try:
        wallet = CompanyWallet.objects.filter(company_id=user.companys_id).only("balance").first()
    except DatabaseError:
        wallet = None
    return {
        "sidebar_wallet": wallet,
        "can_validate_wallet_payment": user.username == "Yrik",
    }
