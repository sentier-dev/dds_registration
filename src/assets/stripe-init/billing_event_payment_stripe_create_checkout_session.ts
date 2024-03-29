(function(){

  interface TCreateCheckoutSessionParams {
    create_checkout_session_url: string;
    STRIPE_PUBLISHABLE_KEY: string;
  }

  window.billing_event_payment_stripe_create_checkout_session =
  function billing_event_payment_stripe_create_checkout_session(params: TCreateCheckoutSessionParams) {
    const {
      STRIPE_PUBLISHABLE_KEY,
      create_checkout_session_url,
    } = params;

    console.log('[billing_event_payment_stripe_create_checkout_session]', {
      STRIPE_PUBLISHABLE_KEY,
      create_checkout_session_url,
    });

    // Initialize Stripe.js
    const stripe = window.Stripe(STRIPE_PUBLISHABLE_KEY);

    initialize();

    // Fetch Checkout Session and retrieve the client secret
    async function initialize() {
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

  }

})();
