/**
 * @module stripe_payment_intents_support.ts
 * @changed 2024.04.04, 00:21
 */
define("stripe-init/stripe_payment_intents_support", ["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.startStripeElementsForm = void 0;
    /** Form action */
    function submitStripeForm(stripe, params, elements, event) {
        var success_url = params.success_url;
        event.preventDefault();
        // @see https://docs.stripe.com/payments/accept-a-payment?platform=web&ui=elements#web-submit-payment
        // const result = await
        stripe.confirmPayment({
            elements: elements,
            confirmParams: {
                return_url: success_url,
            },
        }).then(function (result) {
            var error = result.error;
            if (error) {
                // debugger;
                console.error('[billing_event_stripe_payment_proceed:startStripeElementsForm:submitStripeForm] error', {
                    error: error,
                    event: event,
                    params: params,
                    stripe: stripe,
                });
                // Show error
                var messageContainer = document.querySelector('#error-message');
                if (messageContainer) {
                    messageContainer.textContent = error.message || '';
                }
            }
            else {
                // Success: redirect to success message
                console.log('[billing_event_stripe_payment_proceed:startStripeElementsForm:submitStripeForm] success', {
                    success_url: success_url,
                    event: event,
                    params: params,
                    stripe: stripe,
                });
                debugger;
                window.location.href = success_url;
            }
        }).catch(function (error) {
            console.error('[billing_event_stripe_payment_proceed:startStripeElementsForm:submitStripeForm] error', {
                error: error,
                event: event,
                params: params,
                stripe: stripe,
            });
        });
    }
    /** Start stripe payment form */
    function startStripeElementsForm(params) {
        var STRIPE_PUBLISHABLE_KEY = params.STRIPE_PUBLISHABLE_KEY, 
        // success_url,
        client_secret = params.client_secret;
        // Initialize Stripe.js
        var stripe = window.Stripe(STRIPE_PUBLISHABLE_KEY);
        // @see https://docs.stripe.com/js/elements_object/create_payment_element#payment_element_create-options
        var options = {
            clientSecret: client_secret,
            // TODO: Customize forms (use bootstrap styles)...
            // appearance: {},
        };
        // Set up Stripe.js and Elements to use in checkout form, passing the client secret obtained in a previous step
        var elements = stripe.elements(options);
        // Create and mount the Payment Element
        // @see https://docs.stripe.com/js/elements_object/create_payment_element
        var paymentElement = elements.create('payment');
        paymentElement.mount('#payment-element');
        var form = document.getElementById('payment-form');
        if (!form) {
            var errorText = 'Form node could not be found!';
            var error = new Error(errorText);
            console.log('[billing_event_stripe_payment_proceed:startStripeElementsForm] error', errorText, {
                error: error,
                params: params,
                stripe: stripe,
                options: options,
                elements: elements,
                paymentElement: paymentElement,
                form: form,
            });
            debugger;
            return;
        }
        form.addEventListener('submit', submitStripeForm.bind(null, stripe, params, elements));
    }
    exports.startStripeElementsForm = startStripeElementsForm;
});
/**
 * @module billing_event_stripe_payment_proceed.ts
 * @changed 2024.04.04, 00:21
 */
define("stripe-init/billing_event_stripe_payment_proceed", ["require", "exports", "stripe-init/stripe_payment_intents_support"], function (require, exports, stripe_payment_intents_support_1) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.billing_event_stripe_payment_proceed = void 0;
    exports.billing_event_stripe_payment_proceed = stripe_payment_intents_support_1.startStripeElementsForm;
});
// NOTE: It's possible to use `startStripeElementsForm` directly here.
/**
 * @module billing_membership_stripe_payment_proceed.ts
 * @changed 2024.04.04, 01:15
 */
define("stripe-init/billing_membership_stripe_payment_proceed", ["require", "exports", "stripe-init/stripe_payment_intents_support"], function (require, exports, stripe_payment_intents_support_2) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.billing_membership_stripe_payment_proceed = void 0;
    exports.billing_membership_stripe_payment_proceed = stripe_payment_intents_support_2.startStripeElementsForm;
});
// NOTE: It's possible to use `startStripeElementsForm` directly here.
/**
 * @desc Main js entry point module (scripts)
 * @module src/assets/scripts.ts
 * @changed 2024.04.03, 20:03
 */
define("scripts", ["require", "exports", "stripe-init/billing_event_stripe_payment_proceed", "stripe-init/billing_membership_stripe_payment_proceed"], function (require, exports, billing_event_stripe_payment_proceed_1, billing_membership_stripe_payment_proceed_1) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    // Expose functions to global scope...
    window.billing_event_stripe_payment_proceed = billing_event_stripe_payment_proceed_1.billing_event_stripe_payment_proceed;
    window.billing_membership_stripe_payment_proceed = billing_membership_stripe_payment_proceed_1.billing_membership_stripe_payment_proceed;
    console.log('[scripts] Main client code entry point', {
        billing_event_stripe_payment_proceed: billing_event_stripe_payment_proceed_1.billing_event_stripe_payment_proceed,
        billing_membership_stripe_payment_proceed: billing_membership_stripe_payment_proceed_1.billing_membership_stripe_payment_proceed,
    });
});
/**
 * @module test.ts
 * @changed 2024.04.03, 16:18
 */
(function (window) {
    // console.log('Test', window);
})(window);

//# sourceMappingURL=scripts.js.map
