from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest
from django.shortcuts import redirect, render

from ..core.helpers.dates import this_year
from ..forms import MembershipForm
from ..models import MEMBERSHIP_DATA, Membership, Payment


def membership_application(request: HttpRequest):
    if not request.user:
        messages.error(request, "You have to have an account before you can register for membership")
        return redirect("login")
    if not request.user.is_authenticated:
        messages.error(request, "You have to authenticate your account before you can register for membership")
        return redirect("login")

    try:
        membership = Membership.objects.get(user=request.user)
        if membership.active:
            messages.error(request, "You are already a DdS member")
            return redirect("profile")
    except ObjectDoesNotExist:
        pass

    if request.method == "POST":
        form = MembershipForm(request.POST)

        if form.is_valid():
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
                        "type": form.cleaned_data["membership_type"],
                        "label": MEMBERSHIP_DATA[form.cleaned_data["membership_type"]]["label"]
                    },
                    "method": form.cleaned_data["payment_method"],
                    "price": MEMBERSHIP_DATA[form.cleaned_data["membership_type"]]["price"],
                    "currency": MEMBERSHIP_DATA[form.cleaned_data["membership_type"]]["currency"],
                },
            )
            payment.save()

            try:
                membership = Membership.objects.get(user=request.user)
                membership.mailing_list = form.cleaned_data["mailing_list"]
                membership.membership_type = form.cleaned_data["membership_type"]
                membership.until = this_year()
                membership.payment = payment
                membership.save()
            except ObjectDoesNotExist:
                membership = Membership(
                    user=request.user, membership_type=form.cleaned_data["membership_type"], payment=payment, mailing_list=form.cleaned_data["mailing_list"]
                )
                membership.save()

            if payment.data["method"] == "INVOICE":
                payment.status = "ISSUED"
                payment.data['until'] = membership.until
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
            }
        )

    return render(
        request=request,
        template_name="dds_registration/membership_start.html.django",
        context={"form": form},
    )


# @login_required
# def membership_proceed_success(request: HttpRequest):
#     context = {
#         "action": "membership_proceed_success",
#     }
#     return render(request, "dds_registration/membership_test.html.django", context)


# def send_membership_registration_success_message(request: HttpRequest):
#     """
#     Send successful membership registration message to the user

#     TODO: Send different messages depending on the `payment_method`?
#     """

#     email_body_template = "dds_registration/membership_registration_new_success_message_body.txt"
#     email_subject_template = "dds_registration/membership_registration_new_success_message_subject.txt"

#     user = request.user

#     context = get_membership_invoice_context(request)

#     invoice = context.get("invoice")

#     try:
#         subject = render_to_string(
#             template_name=email_subject_template,
#             context=context,
#             request=request,
#         )
#         subject = " ".join(subject.splitlines()).strip()
#         body = render_to_string(
#             template_name=email_body_template,
#             context=context,
#             request=request,
#         )

#         if invoice.payment_method == "INVOICE" and invoice.status in ("ISSUED", "CREATED"):
#             user.email_user(
#                 subject=subject,
#                 message=body,
#                 attachment_content=create_invoice_pdf(context),
#                 attachment_name="DdS Membership Invoice {}.pdf".format(user.get_full_name()),
#             )
#             invoice.status = "ISSUED"
#             invoice.save()
#         else:
#             user.email_user(subject=subject, message=body)
#     except Exception as err:
#         sError = errorToString(err, show_stacktrace=False)
#         sTraceback = str(traceback.format_exc())
#         debug_data = {
#             "err": err,
#             "traceback": sTraceback,
#         }
#         LOG.error("Caught error %s (re-raising): %s", sError, debug_data)
#         raise err
