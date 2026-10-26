from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from ..core.membership.validity import renewal_until, within_renewal_window
from ..forms import MembershipDetailsForm, MembershipForm
from ..models import MEMBERSHIP_DATA, Membership, Payment


def membership_application(request: HttpRequest):
    if not request.user or not request.user.is_authenticated:
        messages.error(request, "You have to have an account before you can register for membership")
        return redirect("login")

    membership = Membership.objects.filter(user=request.user).first()
    today = date.today()
    current_until = membership.until if membership else None
    if not within_renewal_window(current_until, today, settings.MEMBERSHIP_RENEWAL_WINDOW_DAYS):
        messages.error(
            request,
            f"Your membership is valid until {current_until:%-d %B %Y}; renewal opens "
            f"{settings.MEMBERSHIP_RENEWAL_WINDOW_DAYS} days before that.",
        )
        return redirect("profile")

    if request.method == "POST":
        form = MembershipForm(request.POST)

        if form.is_valid():
            until = renewal_until(current_until, today)
            membership_type = form.cleaned_data["membership_type"]
            payment = Payment(
                status="CREATED",
                data={
                    "user": {
                        "id": request.user.id,
                        "name": form.cleaned_data["name"],
                        "address": form.cleaned_data["address"],
                    },
                    "extra": form.cleaned_data["extra"],
                    "kind": "membership",
                    "membership": {
                        "type": membership_type,
                        "label": MEMBERSHIP_DATA[membership_type]["label"],
                        "organization": form.cleaned_data["organization"],
                        "organization_type": form.cleaned_data["organization_type"],
                    },
                    "method": form.cleaned_data["payment_method"],
                    "price": MEMBERSHIP_DATA[membership_type]["price"],
                    "currency": MEMBERSHIP_DATA[membership_type]["currency"],
                    "until": until.isoformat(),
                },
            )
            payment.save()

            if membership is None:
                membership = Membership(user=request.user, started=today)
            membership.mailing_list = form.cleaned_data["mailing_list"]
            membership.membership_type = membership_type
            membership.organization = form.cleaned_data["organization"]
            membership.organization_type = form.cleaned_data["organization_type"]
            membership.until = until
            membership.payment = payment
            membership.save()

            if payment.data["method"] == "INVOICE":
                payment.status = "ISSUED"
                payment.save()
                payment.email_invoice()
                messages.success(
                    request,
                    f"Your membership has been created! An invoice has been sent to {request.user.email} from events@d-d-s.ch. The invoice can also be downloaded from your profile. Please note your membership is not in force until the invoice is paid.",
                )
                return redirect("profile")
            elif payment.data["method"] == "STRIPE":
                return redirect("payment_stripe", payment_id=payment.id)
    else:
        form = MembershipForm(
            initial={
                "name": request.user.get_full_name(),
                "address": request.user.address,
                "extra": "",
                "organization": membership.organization if membership else "",
                "organization_type": membership.organization_type if membership else "",
            }
        )

    return render(
        request=request,
        template_name="dds_registration/membership/membership_start.html.django",
        context={"form": form},
    )


@login_required
def membership_details(request: HttpRequest):
    membership = get_object_or_404(Membership, user=request.user)
    if request.method == "POST":
        form = MembershipDetailsForm(request.POST, instance=membership)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks, your membership record is complete.")
            return redirect("profile")
    else:
        form = MembershipDetailsForm(instance=membership)
    return render(
        request=request,
        template_name="dds_registration/membership/membership_details.html.django",
        context={"form": form, "membership": membership},
    )
