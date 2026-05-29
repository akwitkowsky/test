# Cost of Meeting 💸

A single-page PWA that ticks up a giant dollar counter showing the live,
accumulated cost of a meeting from the moment you start it.

## Run it

```bash
npm install
npm run dev      # local dev server (Vite prints the URL)
npm run build    # production build into dist/
npm run preview  # serve the production build
npm test         # unit tests for the cost math (node --test)
```

## How it works

- **Inputs** (setup screen): number of people (default 5), average annual
  salary (default $75,000), and an optional advanced field for working hours
  per year (default 2080).
- **The math** lives entirely in [`src/lib/meetingCost.js`](src/lib/meetingCost.js)
  as pure functions with **zero** React/DOM/browser dependencies, so a future
  React Native port can `import` them unchanged:
  - per-person hourly = `salary / hoursPerYear`
  - per-second rate = `(perPersonHourly * numPeople) / 3600`
  - displayed cost = `perSecondRate * secondsElapsed`
- **Timer accuracy:** elapsed time is computed from real timestamps
  (`Date.now()` banked across pause/resume segments), never by counting
  interval ticks, so it can't drift over a long meeting. Each tick recomputes
  the cost from `(now - startTime)`.
- **Flash:** the number briefly flashes red the first time cost crosses
  $100 / $500 / $1000.

## PWA / iPhone home screen

The app ships a web manifest, icons, and a service worker, so it installs and
launches fullscreen.

**Add to your iPhone home screen:**

1. Open the app's URL in **Safari** (must be Safari — Chrome on iOS can't
   install PWAs). If you're running it locally, use `npm run preview` and open
   the network URL it prints from your phone on the same Wi-Fi, or deploy the
   `dist/` folder to any static host (it must be served over **HTTPS** for the
   service worker to register).
2. Tap the **Share** button (the square with the up arrow).
3. Scroll down and tap **Add to Home Screen**.
4. Confirm the name ("Meeting Cost") and tap **Add**.
5. Launch it from the new home-screen icon — it opens fullscreen with no
   browser chrome, and works offline.

## Out of scope

No calendar integration, salary lookup, accounts, or storage. Everything is in
memory and resets on refresh (the PWA install itself persists).
