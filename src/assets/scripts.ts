/**
 * @desc Main js entry point module (scripts)
 * @module src/assets/scripts.ts
 * @changed 2024.04.03, 20:03
 */

import { billing_event_stripe_payment_proceed } from './stripe-init/billing_event_stripe_payment_proceed';
import { billing_membership_stripe_payment_proceed } from './stripe-init/billing_membership_stripe_payment_proceed';

// Expose functions to global scope...
window.billing_event_stripe_payment_proceed = billing_event_stripe_payment_proceed;
window.billing_membership_stripe_payment_proceed = billing_membership_stripe_payment_proceed;

/*
 * console.log('[scripts] Main client code entry point', {
 *   billing_event_stripe_payment_proceed,
 *   billing_membership_stripe_payment_proceed,
 * });
 */
