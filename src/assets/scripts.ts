/**
 * @desc Main js entry point module (scripts)
 * @module src/assets/scripts.ts
 * @changed 2024.04.04, 16:06
 */

/* NOTE: These modules are unused. Used only
 * `src/assets/stripe-init/stripe_payment_intents_support.ts`, via requirejs,
 * without exposing to global scope.
 *
 * import { billing_event_stripe_payment_proceed } from './stripe-init/billing_event_stripe_payment_proceed';
 * import { billing_membership_stripe_payment_proceed } from './stripe-init/billing_membership_stripe_payment_proceed';
 *
 * // Expose functions to global scope...
 * window.billing_event_stripe_payment_proceed = billing_event_stripe_payment_proceed;
 * window.billing_membership_stripe_payment_proceed = billing_membership_stripe_payment_proceed;
 *
 * console.log('[scripts] Main client code entry point', {
 *   billing_event_stripe_payment_proceed,
 *   billing_membership_stripe_payment_proceed,
 * });
 */
