/**
 * @module billing_event_stripe_payment_proceed.ts
 * @changed 2024.04.03, 17:13
 */

import type { StripeElements, StripeElementsOptionsClientSecret, StripePaymentElement } from '@stripe/stripe-js/dist/stripe-js';

export function billing_event_stripe_payment_proceed(params: TCreateCheckoutSessionParams) {
  const {
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
  // initializeCheckout(); // Old api

  /** Start stripe payment form */
  function startElements() {
    // @see https://docs.stripe.com/js/elements_object/create_payment_element#payment_element_create-options
    const options: StripeElementsOptionsClientSecret = {
      clientSecret: client_secret,
      // Fully customizable with appearance API.
      // appearance: {[>...<]},
    };
    console.log('[billing_event_stripe_payment_proceed:startElements] started', {
      options,
      STRIPE_PUBLISHABLE_KEY,
      client_secret,
      success_url,
      stripe,
      params,
    });
    // debugger;

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

    console.log('[billing_event_stripe_payment_proceed:startElements] created', {
      paymentElement,
      elements,
      form,
    });
    // NOTE: Stripe elements couldn't start if we have debugger statements here
    // debugger;

    form.addEventListener('submit', submitForm.bind(null, elements));
  }

  /** Form action */
  async function submitForm(elements: StripeElements, event: SubmitEvent) {
      event.preventDefault();

      console.log('[billing_event_stripe_payment_proceed:startElements:submit] check', {
        event,
        params,
        stripe,
        elements,
      });
      debugger;

      // @see https://docs.stripe.com/payments/accept-a-payment?platform=web&ui=elements#web-submit-payment
      const { error } = await stripe.confirmPayment({
        //`Elements` instance that was used to create the Payment Element
        elements,
        confirmParams: {
          return_url: success_url, // 'https://example.com/order/123/complete',
        },
      });

      console.log('[billing_event_stripe_payment_proceed:startElements:submit] checked', {
        error,
        event,
        params,
        stripe,
      });
      debugger;

      if (error) {
        console.log('[billing_event_stripe_payment_proceed:startElements:submit] error', {
          error,
          event,
          params,
          stripe,
        });
        debugger;

        // This point will only be reached if there is an immediate error when
        // confirming the payment. Show error to your customer (for example, payment
        // details incomplete)
        const messageContainer = document.querySelector('#error-message');
        if (messageContainer) {
          messageContainer.textContent = error.message || '';
        }
      } else {
        // Your customer will be redirected to your `return_url`. For some payment
        // methods like iDEAL, your customer will be redirected to an intermediate
        // site first to authorize the payment, then redirected to the `return_url`.
        console.log('[billing_event_stripe_payment_proceed:startElements:submit] success', {
          success_url,
          event,
          params,
          stripe,
        });
        debugger;
        window.location.href = success_url;
      }
  }

  /* OBSOLETE: Fetch Checkout Session and retrieve the client secret
  async function initializeCheckout() {
    const fetchClientSecret = async () => {
      const response = await fetch(create_checkout_session_url, {
        method: 'POST',
      });
      const { clientSecret } = await response.json();
      return clientSecret;
    };

    // Initialize Checkout
    const checkout = await stripe.initEmbeddedCheckout({
      fetchClientSecret,
    });

    // Mount Checkout
    checkout.mount('#checkout');
  }
  */

}
