import React from 'react';
import { createRoot } from 'react-dom/client';
import MeetingCostCounter from './MeetingCostCounter.jsx';
import './styles.css';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <MeetingCostCounter />
  </React.StrictMode>
);

// Register the service worker so the app works offline / installs as a PWA.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register(`${import.meta.env.BASE_URL}sw.js`)
      .catch(() => {
        /* offline support is best-effort; ignore registration failures */
      });
  });
}
