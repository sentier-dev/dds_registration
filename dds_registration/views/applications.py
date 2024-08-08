from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.text import capfirst
from djf_surveys.models import UserAnswer
from djf_surveys.views import CreateSurveyFormView, EditSurveyFormView

from ..models import Registration


class CreateApplicationFormView(CreateSurveyFormView):
    title_page = "Create application"

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        self.object = self.get_object()
        existing_application = UserAnswer.objects.filter(survey=self.object, user=request.user).exists()

        if form.is_valid():
            form.save()

            if not (hasattr(self.object, "for_event") and self.object.for_event):
                # Just a survey, not an application
                messages.success(
                    self.request,
                    "%(page_action_name)s succeeded." % dict(page_action_name=capfirst(self.title_page.lower())),
                )
                return redirect("profile")
            elif existing_application:
                # Application already linked to registration
                # Just updated the answers
                messages.success(self.request, "Application form answers edited successfully")
                return redirect("profile")
            else:
                event = self.object.for_event
                created_application = UserAnswer.objects.get(survey=self.object, user=request.user)
                Registration(
                    event=event,
                    application=created_application,
                    status="SUBMITTED",
                    user=request.user,
                    send_update_emails=True,
                ).save()
                messages.success(request, f"You have successfully applied for {event.title}.")
                if event.application_submitted_email:
                    request.user.email_user(
                        subject=f"Application submitted for {event.title}",
                        message=event.application_submitted_email.strip()
                        + "\nYou can edit your answers at:\n"
                        + request.build_absolute_uri(reverse("djf_surveys:edit", args=[created_application.id])),
                    )
                return redirect("profile")
        else:
            messages.error(self.request, "Please correct the indicated errors")
            return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        from djf_surveys.models import UserAnswer

        survey = self.get_object()
        # handle if survey can_anonymous_user
        if not request.user.is_authenticated and not survey.can_anonymous_user:
            messages.warning(request, "Sorry, you must be logged in to fill out the application.")
            return redirect("profile")

        # handle if user have answer survey
        if (
            request.user.is_authenticated
            and not survey.duplicate_entry
            and UserAnswer.objects.filter(survey=survey, user=request.user).exists()
        ):
            messages.warning(
                request, "You have submitted this application, and answers can't be edited after submission."
            )
            return redirect("profile")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("profile")


class EditApplicationFormView(EditSurveyFormView):
    title_page = "Edit application"

    def dispatch(self, request, *args, **kwargs):
        # handle if user not same
        user_answer = self.get_object()
        if user_answer.user != request.user or not user_answer.survey.editable:
            messages.warning(request, "You can't edit this survey. You don't have permission.")
            return redirect("profile")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse("profile")
