from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .forms import PaymentValidationForm
from .models import CompanyWallet
from .services import deposit


DEFAULT_PAYMENT_URL = "https://paylink.tbank.ru/6c2772a4-247c-40a7-9a9f-bc30990d346b"


@login_required
def wallet_detail(request):
    if not request.user.companys_id:
        messages.warning(request, "К вашему аккаунту не привязана компания")
        return redirect("current_applications")

    wallet, _ = CompanyWallet.objects.get_or_create(company_id=request.user.companys_id)
    payment_url = getattr(settings, "WALLET_PAYMENT_URL", settings.CLIENT_PAYMENT_URL or DEFAULT_PAYMENT_URL)
    return render(
        request,
        "wallet/wallet_detail.html",
        {
            "wallet": wallet,
            "transactions": wallet.transactions.all(),
            "payment_url": payment_url,
            "payment_qr_url": (
                "https://api.qrserver.com/v1/create-qr-code/"
                f"?size=260x260&margin=12&data={quote(payment_url, safe='')}"
            ),
            "can_validate_payment": request.user.username == "Yrik",
        },
    )


@login_required
def validate_payment(request):
    if request.user.username != "Yrik":
        raise PermissionDenied

    form = PaymentValidationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        wallet, _ = CompanyWallet.objects.get_or_create(company=form.cleaned_data["company"])
        deposit(wallet, form.cleaned_data["amount"], form.cleaned_data["comment"])
        messages.success(
            request,
            f"Баланс компании «{form.cleaned_data['company'].title}» успешно пополнен",
        )
        return redirect("wallet_validate_payment")

    return render(request, "wallet/payment_validation.html", {"form": form})
