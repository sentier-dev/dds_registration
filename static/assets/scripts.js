var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
/**
 * @module billing_event_stripe_payment_proceed.ts
 * @changed 2024.04.03, 23:01
 */
define("stripe-init/billing_event_stripe_payment_proceed", ["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.billing_event_stripe_payment_proceed = void 0;
    function billing_event_stripe_payment_proceed(params) {
        var 
        // \<\(STRIPE_PUBLISHABLE_KEY\|success_url\|client_secret\)\>
        STRIPE_PUBLISHABLE_KEY = params.STRIPE_PUBLISHABLE_KEY, success_url = params.success_url, client_secret = params.client_secret;
        console.log('[billing_event_stripe_payment_proceed]', {
            STRIPE_PUBLISHABLE_KEY: STRIPE_PUBLISHABLE_KEY,
            client_secret: client_secret,
            success_url: success_url,
        });
        // Initialize Stripe.js
        var stripe = window.Stripe(STRIPE_PUBLISHABLE_KEY);
        startElements();
        /** Start stripe payment form */
        function startElements() {
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
                console.log('[billing_event_stripe_payment_proceed:startElements] error', errorText, {
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
            form.addEventListener('submit', submitForm.bind(null, elements));
        }
        /** Form action */
        function submitForm(elements, event) {
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
                    console.error('[billing_event_stripe_payment_proceed:startElements:submitForm] error', {
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
                    console.log('[billing_event_stripe_payment_proceed:startElements:submitForm] success', {
                        success_url: success_url,
                        event: event,
                        params: params,
                        stripe: stripe,
                    });
                    debugger;
                    window.location.href = success_url;
                }
            }).catch(function (error) {
                console.error('[billing_event_stripe_payment_proceed:startElements:submitForm] error', {
                    error: error,
                    event: event,
                    params: params,
                    stripe: stripe,
                });
            });
        }
    }
    exports.billing_event_stripe_payment_proceed = billing_event_stripe_payment_proceed;
});
/**
 * @module billing_membership_stripe_payment_proceed.ts
 * @changed 2024.04.03, 16:18
 */
define("stripe-init/billing_membership_stripe_payment_proceed", ["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    exports.billing_membership_stripe_payment_proceed = void 0;
    function billing_membership_stripe_payment_proceed(params) {
        var STRIPE_PUBLISHABLE_KEY = params.STRIPE_PUBLISHABLE_KEY, success_url = params.success_url;
        console.log('[billing_membership_stripe_payment_proceed]', {
            STRIPE_PUBLISHABLE_KEY: STRIPE_PUBLISHABLE_KEY,
            success_url: success_url,
        });
        // Initialize Stripe.js
        var stripe = window.Stripe(STRIPE_PUBLISHABLE_KEY);
        initialize();
        // Fetch Checkout Session and retrieve the client secret
        function initialize() {
            return __awaiter(this, void 0, void 0, function () {
                var fetchClientSecret, checkout;
                var _this = this;
                return __generator(this, function (_a) {
                    switch (_a.label) {
                        case 0:
                            fetchClientSecret = function () { return __awaiter(_this, void 0, void 0, function () {
                                var response, clientSecret;
                                return __generator(this, function (_a) {
                                    switch (_a.label) {
                                        case 0: return [4 /*yield*/, fetch(success_url, {
                                                method: 'POST',
                                            })];
                                        case 1:
                                            response = _a.sent();
                                            return [4 /*yield*/, response.json()];
                                        case 2:
                                            clientSecret = (_a.sent()).clientSecret;
                                            return [2 /*return*/, clientSecret];
                                    }
                                });
                            }); };
                            return [4 /*yield*/, stripe.initEmbeddedCheckout({
                                    fetchClientSecret: fetchClientSecret,
                                })];
                        case 1:
                            checkout = _a.sent();
                            // Mount Checkout
                            checkout.mount('#checkout');
                            return [2 /*return*/];
                    }
                });
            });
        }
    }
    exports.billing_membership_stripe_payment_proceed = billing_membership_stripe_payment_proceed;
});
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
