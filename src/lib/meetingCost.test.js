// Tests for the pure business logic. Run with: npm test  (node --test)
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  hourlyRate,
  ratePerSecond,
  costForElapsed,
  costFromInputs,
  elapsedSeconds,
  ratePerMinute,
  formatCurrency,
  formatElapsed,
  thresholdCrossed,
  DEFAULTS,
} from './meetingCost.js';

test('hourlyRate divides salary by hours', () => {
  assert.equal(hourlyRate(75000, 2080), 75000 / 2080);
  assert.equal(hourlyRate(50000, 0), 0); // guard against divide-by-zero
});

test('ratePerSecond combines people and converts hours to seconds', () => {
  // 1 person, $3600/yr over 3600 hours => $1/hr => $1/3600 per second
  assert.equal(ratePerSecond(1, 3600, 3600), 1 / 3600);
  // scales linearly with people
  assert.equal(ratePerSecond(4, 3600, 3600), 4 / 3600);
});

test('costForElapsed multiplies rate by seconds', () => {
  assert.equal(costForElapsed(2, 10), 20);
});

test('costFromInputs end-to-end', () => {
  // 5 people, $75k, 2080h, after 1 hour (3600s)
  const perPersonHourly = 75000 / 2080;
  const expected = perPersonHourly * 5; // one hour of 5 people
  const got = costFromInputs(
    { numPeople: 5, avgSalary: 75000, hoursPerYear: 2080 },
    3600
  );
  assert.ok(Math.abs(got - expected) < 1e-9);
});

test('defaults yield a sane per-minute burn', () => {
  const ps = ratePerSecond(
    DEFAULTS.numPeople,
    DEFAULTS.avgSalary,
    DEFAULTS.hoursPerYear
  );
  // 5 people at ~$36/hr each ~= $180/hr ~= $3/min
  assert.ok(ratePerMinute(ps) > 2.9 && ratePerMinute(ps) < 3.1);
});

test('elapsedSeconds uses timestamps and banks accumulated ms', () => {
  assert.equal(elapsedSeconds(1000, 4000), 3); // 3000ms live
  assert.equal(elapsedSeconds(1000, 4000, 2000), 5); // + 2000ms banked
  assert.equal(elapsedSeconds(null, 4000, 7000), 7); // paused: only banked
  assert.equal(elapsedSeconds(5000, 4000), 0); // clamps negative drift
});

test('formatCurrency: two decimals + thousands separators', () => {
  assert.equal(formatCurrency(1234.5), '$1,234.50');
  assert.equal(formatCurrency(0), '$0.00');
  assert.equal(formatCurrency(NaN), '$0.00');
});

test('formatElapsed: mm:ss with hours rolling into minutes', () => {
  assert.equal(formatElapsed(0), '00:00');
  assert.equal(formatElapsed(65), '01:05');
  assert.equal(formatElapsed(3900), '65:00');
});

test('thresholdCrossed fires once per crossing, highest wins', () => {
  assert.equal(thresholdCrossed(99, 101), 100);
  assert.equal(thresholdCrossed(101, 150), null); // already past 100
  assert.equal(thresholdCrossed(50, 600), 500); // jumps past 100 and 500
  assert.equal(thresholdCrossed(999, 1001), 1000);
});
