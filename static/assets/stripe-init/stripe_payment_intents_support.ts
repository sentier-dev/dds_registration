/**
 * @module stripe_payment_intents_support.ts
 * @changed 2024.04.04, 00:21
 */

import type {
  Stripe,
  StripeElements,
  StripeElementsOptionsClientSecret,
  StripeError,
  StripePaymentElement,
} from '@stripe/stripe-js/dist/stripe-js';

/** Form action */
function submitStripeForm(
  stripe: Stripe,
  params: TCreateCheckoutSessionParams,
  elements: StripeElements,
  event: SubmitEvent,
) {
  const { success_url } = params;

  event.preventDefault();

  // @see https://docs.stripe.com/payments/accept-a-payment?platform=web&ui=elements#web-submit-payment
  // TODO: Show 'busy' spinner at stripe interaction begin? (It could take some time.)
  stripe
    .confirmPayment({
      elements,
      confirmParams: {
        return_url: success_url,
      },
    })
    .then((result) => {
      const error: StripeError = result.error;

      if (error) {
        console.error(
          '[stripe_payment_intents_support:startStripeElementsForm:submitStripeForm] error',
          {
            error,
            event,
            params,
            stripe,
          },
        );

        // Show error
        const messageContainer = document.querySelector('#error-message');
        if (messageContainer) {
          messageContainer.textContent = error.message || '';
        }
      } else {
        // Success: redirect to success message
        console.log(
          '[stripe_payment_intents_support:startStripeElementsForm:submitStripeForm] success',
          {
            success_url,
            event,
            params,
            stripe,
          },
        );
        window.location.href = success_url;
      }
    })
    .catch((error) => {
      console.error(
        '[stripe_payment_intents_support:startStripeElementsForm:submitStripeForm] error',
        {
          error,
          event,
          params,
          stripe,
        },
      );
    });
}

/** Start stripe payment form */
export function startStripeElementsForm(params: TCreateCheckoutSessionParams) {
  const {
    STRIPE_PUBLISHABLE_KEY,
    // success_url,
    client_secret,
  } = params;

  // Initialize Stripe.js
  const stripe: Stripe = window.Stripe(STRIPE_PUBLISHABLE_KEY);

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
    const errorText = 'Form node could not be found!';
    const error = new Error(errorText);
    console.error('[stripe_payment_intents_support:startStripeElementsForm] error', errorText, {
      error,
      params,
      stripe,
      options,
      elements,
      paymentElement,
      form,
    });
    // eslint-disable-next-line no-debugger
    debugger;
    return;
  }

  form.addEventListener('submit', submitStripeForm.bind(null, stripe, params, elements));
}
