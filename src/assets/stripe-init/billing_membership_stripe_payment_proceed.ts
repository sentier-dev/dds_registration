/**
 * @module billing_membership_stripe_payment_proceed.ts
 * @changed 2024.04.03, 16:18
 */

(function(){

  window.billing_membership_stripe_payment_proceed =
  function billing_membership_stripe_payment_proceed(params: TCreateCheckoutSessionParams) {
    const {
      STRIPE_PUBLISHABLE_KEY,
      success_url,
    } = params;

    console.log('[billing_membership_stripe_payment_proceed]', {
      STRIPE_PUBLISHABLE_KEY,
      success_url,
    });

    // Initialize Stripe.js
    const stripe = window.Stripe(STRIPE_PUBLISHABLE_KEY);

    initialize();

    // Fetch Checkout Session and retrieve the client secret
    async function initialize() {
      const fetchClientSecret = async () => {
        const response = await fetch(success_url, {
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
