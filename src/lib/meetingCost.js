/**
 * meetingCost.js
 *
 * Pure, framework-agnostic business logic for the "cost of meeting" counter.
 *
 * NOTHING in this file touches React, the DOM, timers, or any browser API.
 * It is plain data-in / data-out so a future React Native port (or a CLI, or
 * a test suite) can import these functions unchanged.
 */

/** Sensible defaults, shared by every front end. */
export const DEFAULTS = Object.freeze({
  numPeople: 5,
  avgSalary: 75000,
  hoursPerYear: 2080, // 40h/week * 52 weeks
});

/** Cost thresholds that should trigger a visual "flash" when first crossed. */
export const FLASH_THRESHOLDS = Object.freeze([100, 500, 1000]);

/**
 * Per-person hourly rate.
 * @param {number} salary       annual salary in dollars
 * @param {number} hoursPerYear working hours per year
 * @returns {number} dollars per hour for one person
 */
export function hourlyRate(salary, hoursPerYear) {
  if (!hoursPerYear) return 0;
  return salary / hoursPerYear;
}

/**
 * Combined cost burn rate, in dollars per second, across all attendees.
 * @param {number} numPeople    number of attendees
 * @param {number} salary       annual salary in dollars (per person, averaged)
 * @param {number} hoursPerYear working hours per year
 * @returns {number} dollars per second
 */
export function ratePerSecond(numPeople, salary, hoursPerYear) {
  return (hourlyRate(salary, hoursPerYear) * numPeople) / 3600;
}

/**
 * Accumulated meeting cost.
 * @param {number} perSecondRate dollars per second (see ratePerSecond)
 * @param {number} secondsElapsed seconds since the meeting started
 * @returns {number} total dollars spent so far
 */
export function costForElapsed(perSecondRate, secondsElapsed) {
  return perSecondRate * secondsElapsed;
}

/**
 * Convenience helper: compute cost directly from inputs + elapsed seconds.
 * @param {{numPeople:number, avgSalary:number, hoursPerYear:number}} inputs
 * @param {number} secondsElapsed
 * @returns {number} total dollars spent so far
 */
export function costFromInputs(inputs, secondsElapsed) {
  const { numPeople, avgSalary, hoursPerYear } = inputs;
  return costForElapsed(
    ratePerSecond(numPeople, avgSalary, hoursPerYear),
    secondsElapsed
  );
}

/**
 * Elapsed seconds derived from real timestamps. This is the source of truth:
 * the UI must recompute from (now - startTime) rather than counting ticks,
 * so interval drift never accumulates over a long meeting.
 *
 * @param {number} startTime      Date.now() captured when the meeting started
 * @param {number} now            current Date.now()
 * @param {number} [accumulatedMs=0] milliseconds banked from prior run
 *                                   segments (used to support pause/resume)
 * @returns {number} seconds elapsed (fractional)
 */
export function elapsedSeconds(startTime, now, accumulatedMs = 0) {
  const liveMs = startTime == null ? 0 : Math.max(0, now - startTime);
  return (accumulatedMs + liveMs) / 1000;
}

/**
 * Format dollars as a fixed-2-decimal currency string, e.g. "$1,234.56".
 * @param {number} amount
 * @returns {string}
 */
export function formatCurrency(amount) {
  const safe = Number.isFinite(amount) ? amount : 0;
  return (
    '$' +
    safe.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  );
}

/**
 * Format a duration as mm:ss (hours roll into minutes, e.g. 1h05m -> "65:00").
 * @param {number} totalSeconds
 * @returns {string}
 */
export function formatElapsed(totalSeconds) {
  const whole = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(whole / 60);
  const seconds = whole % 60;
  const pad = (n) => String(n).padStart(2, '0');
  return `${pad(minutes)}:${pad(seconds)}`;
}

/**
 * Per-minute burn rate, derived from the per-second rate.
 * @param {number} perSecondRate dollars per second
 * @returns {number} dollars per minute
 */
export function ratePerMinute(perSecondRate) {
  return perSecondRate * 60;
}

/**
 * Given a previous cost and a current cost, return any flash threshold that was
 * crossed between them (so the UI can flash exactly once per threshold).
 * @param {number} prevCost
 * @param {number} nextCost
 * @param {number[]} [thresholds=FLASH_THRESHOLDS]
 * @returns {number|null} the highest threshold crossed this step, or null
 */
export function thresholdCrossed(prevCost, nextCost, thresholds = FLASH_THRESHOLDS) {
  let crossed = null;
  for (const t of thresholds) {
    if (prevCost < t && nextCost >= t) crossed = t;
  }
  return crossed;
}
