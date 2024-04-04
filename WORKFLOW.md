# User registration

# Register for an event

User must be logged in.

User either selects a public event in the index page or pastes a private event URL.

* Request type: `GET`
* URL: `/event/<str:event_code>/registration/new`
* View: `views/event_registration.py:event_registration_new`
* Database changes: *None*
* Email: *None*

If the form elements related to registration are correctly filled out, the user is redirected.

* Request type: `GET`
* URL: `/billing/event/<str:event_code>`
* View: `views/billing_event.py:billing_event`
* Database changes: *None*
* Email: *None*

The user needs to fill out a registration form, including payment method (bank transfer or credit card). Submitting a form emits a `POST` request to the same method.

* Request type: `POST`
* URL: `/billing/event/<str:event_code>`
* View: `views/billing_event.py:billing_event`
* Database changes:
    * Creates an instance of `Payment`
* Email: *None*

There is also a form for the other details needed for correct billing. Upon successful form submission, the user is redirected. The redirection is based on the form `payment_method`.

## Credit card payment

* URL: `billing/event/<str:event_code>/payment/stripe/proceed`
* View: `views/billing_event_stripe.py:billing_event_stripe_payment_proceed`
* Database changes:
* Emails:

Users enters their credit card details. When there is no error,
