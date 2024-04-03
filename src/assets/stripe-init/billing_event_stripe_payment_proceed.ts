/**
 * @module billing_event_stripe_payment_proceed.ts
 * @changed 2024.04.03, 23:01
 */

import type {
  StripeElements,
  StripeElementsOptionsClientSecret,
  StripeError,
  StripePaymentElement,
} from '@stripe/stripe-js/dist/stripe-js';

export function billing_event_stripe_payment_proceed(params: TCreateCheckoutSessionParams) {
  const {
    // \<\(STRIPE_PUBLISHABLE_KEY\|success_url\|client_secret\)\>

    STRIPE_PUBLISHABLE_KEY,
    success_url,
    client_secret,
  } = params;

  console.log('[billing_event_stripe_payment_proceed]', {
    STRIPE_PUBLISHABLE_KEY,
    client_secret,
    success_url,
  });

  // Initialize Stripe.js
  const stripe = window.Stripe(STRIPE_PUBLISHABLE_KEY);

  startElements();

  /** Start stripe payment form */
  function startElements() {
    // @see https://docs.stripe.com/js/elements_object/create_payment_element#payment_element_create-options
    const options: StripeElementsOptionsClientSecret = {
      clientSecret: client_secret,
      // TODO: Customize forms (use bootstrap styles)...
      // appearance: {},
    };

    // Set up Stripe.js and Elements to use in checkout form, passing the client secret obtained in a previous step
    const elements: StripeElements = stripe.elements(options);

    // Create and mount the Payment Element
    // @see https://docs.stripe.com/js/elements_object/create_payment_element
    const paymentElement: StripePaymentElement = elements.create('payment');
    paymentElement.mount('#payment-element');

    const form = document.getElementById('payment-form');

    if (!form) {
      const errorText = 'Form node could not be found!'
      const error = new Error(errorText);
      console.log('[billing_event_stripe_payment_proceed:startElements] error', errorText, {
        error,
        params,
        stripe,
        options,
        elements,
        paymentElement,
        form,
      });
      debugger;
      return;
    }

    form.addEventListener('submit', submitForm.bind(null, elements));
  }

  /** Form action */
  function submitForm(elements: StripeElements, event: SubmitEvent) {
    event.preventDefault();

    // @see https://docs.stripe.com/payments/accept-a-payment?platform=web&ui=elements#web-submit-payment
    // const result = await
    stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: success_url,
      },
    }).then((result) => {
      const error: StripeError = result.error;

      if (error) {
        // debugger;
        console.error('[billing_event_stripe_payment_proceed:startElements:submitForm] error', {
          error,
          event,
          params,
          stripe,
        });

        // Show error
        const messageContainer = document.querySelector('#error-message');
        if (messageContainer) {
          messageContainer.textContent = error.message || '';
        }
      } else {
        // Success: redirect to success message
        console.log('[billing_event_stripe_payment_proceed:startElements:submitForm] success', {
          success_url,
          event,
          params,
          stripe,
        });
        debugger;
        window.location.href = success_url;
      }
    }).catch((error) => {
        console.error('[billing_event_stripe_payment_proceed:startElements:submitForm] error', {
          error,
          event,
          params,
          stripe,
        });
    });
  }

}
