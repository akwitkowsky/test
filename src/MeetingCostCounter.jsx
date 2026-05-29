import React, { useEffect, useRef, useState } from 'react';
import {
  DEFAULTS,
  ratePerSecond,
  ratePerMinute,
  costForElapsed,
  elapsedSeconds,
  formatCurrency,
  formatElapsed,
  thresholdCrossed,
} from './lib/meetingCost.js';

/**
 * MeetingCostCounter
 *
 * One self-contained component. All math lives in ./lib/meetingCost.js — this
 * file is purely the React/JSX presentation layer, so the logic can be reused
 * by a React Native port without change.
 *
 * Timer accuracy: we never count ticks. We bank elapsed time in `accumulatedMs`
 * across pause/resume segments and stamp `startTime = Date.now()` whenever the
 * clock is running. Every tick recomputes cost from real wall-clock elapsed.
 */
export default function MeetingCostCounter() {
  // ---- setup inputs (strings so the fields can be cleared while typing) ----
  const [numPeople, setNumPeople] = useState(String(DEFAULTS.numPeople));
  const [avgSalary, setAvgSalary] = useState(String(DEFAULTS.avgSalary));
  const [hoursPerYear, setHoursPerYear] = useState(String(DEFAULTS.hoursPerYear));
  const [showAdvanced, setShowAdvanced] = useState(false);

  // ---- timer state ----
  // phase: 'setup' | 'running' | 'paused'
  const [phase, setPhase] = useState('setup');
  const [startTime, setStartTime] = useState(null); // Date.now() of current run segment
  const [accumulatedMs, setAccumulatedMs] = useState(0); // banked from prior segments
  const [elapsed, setElapsed] = useState(0); // seconds, recomputed each tick
  const [flash, setFlash] = useState(false);

  // numeric, sanitized inputs used by the math
  const inputs = {
    numPeople: Math.max(0, Number(numPeople) || 0),
    avgSalary: Math.max(0, Number(avgSalary) || 0),
    hoursPerYear: Math.max(1, Number(hoursPerYear) || DEFAULTS.hoursPerYear),
  };

  const perSecond = ratePerSecond(
    inputs.numPeople,
    inputs.avgSalary,
    inputs.hoursPerYear
  );
  const cost = costForElapsed(perSecond, elapsed);

  // refs to detect threshold crossings and clear the flash timeout
  const prevCostRef = useRef(0);
  const flashTimeoutRef = useRef(null);

  // ---- the tick: recompute elapsed from real timestamps every ~1s ----
  useEffect(() => {
    if (phase !== 'running') return;

    let raf = null;
    const tick = () => {
      const secs = elapsedSeconds(startTime, Date.now(), accumulatedMs);
      setElapsed(secs);
    };

    tick(); // update immediately on (re)start so there's no blank second
    const id = setInterval(tick, 250); // sub-second cadence keeps it smooth
    return () => {
      clearInterval(id);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [phase, startTime, accumulatedMs]);

  // ---- flash the number red when a threshold is first crossed ----
  useEffect(() => {
    const crossed = thresholdCrossed(prevCostRef.current, cost);
    prevCostRef.current = cost;
    if (crossed != null) {
      setFlash(true);
      if (flashTimeoutRef.current) clearTimeout(flashTimeoutRef.current);
      flashTimeoutRef.current = setTimeout(() => setFlash(false), 900);
    }
  }, [cost]);

  useEffect(() => {
    return () => {
      if (flashTimeoutRef.current) clearTimeout(flashTimeoutRef.current);
    };
  }, []);

  // ---- controls ----
  function handleStart() {
    prevCostRef.current = 0;
    setAccumulatedMs(0);
    setElapsed(0);
    setStartTime(Date.now());
    setPhase('running');
  }

  function handlePause() {
    // bank the current segment, then stop the clock
    const banked = accumulatedMs + Math.max(0, Date.now() - startTime);
    setAccumulatedMs(banked);
    setElapsed(banked / 1000);
    setStartTime(null);
    setPhase('paused');
  }

  function handleResume() {
    setStartTime(Date.now());
    setPhase('running');
  }

  function handleReset() {
    if (flashTimeoutRef.current) clearTimeout(flashTimeoutRef.current);
    prevCostRef.current = 0;
    setStartTime(null);
    setAccumulatedMs(0);
    setElapsed(0);
    setFlash(false);
    setPhase('setup');
  }

  // ---- render ----
  if (phase === 'setup') {
    return (
      <div className="screen setup">
        <h1 className="title">Cost of Meeting</h1>
        <p className="subtitle">See the money burn in real time.</p>

        <label className="field">
          <span>Number of people</span>
          <input
            type="number"
            inputMode="numeric"
            min="0"
            value={numPeople}
            onChange={(e) => setNumPeople(e.target.value)}
          />
        </label>

        <label className="field">
          <span>Average annual salary</span>
          <div className="prefixed">
            <span className="prefix">$</span>
            <input
              type="number"
              inputMode="numeric"
              min="0"
              value={avgSalary}
              onChange={(e) => setAvgSalary(e.target.value)}
            />
          </div>
        </label>

        <button
          type="button"
          className="link-toggle"
          onClick={() => setShowAdvanced((v) => !v)}
        >
          {showAdvanced ? '− Hide advanced' : '+ Advanced'}
        </button>

        {showAdvanced && (
          <label className="field">
            <span>Working hours per year</span>
            <input
              type="number"
              inputMode="numeric"
              min="1"
              value={hoursPerYear}
              onChange={(e) => setHoursPerYear(e.target.value)}
            />
          </label>
        )}

        <button type="button" className="start-btn" onClick={handleStart}>
          Start
        </button>

        <p className="hint">
          Burn rate: {formatCurrency(ratePerMinute(perSecond))}/min
        </p>
      </div>
    );
  }

  // running or paused
  return (
    <div className="screen running">
      <div className={`counter${flash ? ' flash' : ''}`}>
        {formatCurrency(cost)}
      </div>

      <div className="meta">
        <span>{formatElapsed(elapsed)} elapsed</span>
        <span className="dot">•</span>
        <span>{formatCurrency(ratePerMinute(perSecond))}/min</span>
      </div>

      {phase === 'paused' && <div className="paused-tag">Paused</div>}

      <div className="controls">
        {phase === 'running' ? (
          <button type="button" className="ctrl" onClick={handlePause}>
            Pause
          </button>
        ) : (
          <button type="button" className="ctrl primary" onClick={handleResume}>
            Resume
          </button>
        )}
        <button type="button" className="ctrl" onClick={handleReset}>
          Reset
        </button>
      </div>
    </div>
  );
}
