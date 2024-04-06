/**
 * @desc Main js entry point module (scripts)
 * @module src/assets/scripts.ts
 * @changed 2024.04.06, 22:00
 */
define("scripts", ["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
});
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
        // TODO: Show 'busy' spinner at stripe interaction begin? (It could take some time.)
        stripe
            .confirmPayment({
            elements: elements,
            confirmParams: {
                return_url: success_url,
            },
        })
            .then(function (result) {
            var error = result.error;
            if (error) {
                console.error('[stripe_payment_intents_support:startStripeElementsForm:submitStripeForm] error', {
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
                console.log('[stripe_payment_intents_support:startStripeElementsForm:submitStripeForm] success', {
                    success_url: success_url,
                    event: event,
                    params: params,
                    stripe: stripe,
                });
                window.location.href = success_url;
            }
        })
            .catch(function (error) {
            console.error('[stripe_payment_intents_support:startStripeElementsForm:submitStripeForm] error', {
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
            console.error('[stripe_payment_intents_support:startStripeElementsForm] error', errorText, {
                error: error,
                params: params,
                stripe: stripe,
                options: options,
                elements: elements,
                paymentElement: paymentElement,
                form: form,
            });
            // eslint-disable-next-line no-debugger
            debugger;
            return;
        }
        form.addEventListener('submit', submitStripeForm.bind(null, stripe, params, elements));
    }
    exports.startStripeElementsForm = startStripeElementsForm;
});
/**
 * @module test.ts
 * @changed 2024.04.04, 16:19
 */
// console.log('Test', window);

//# sourceMappingURL=scripts.js.map
