import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Self-contained SPA build. No backend, no env config required.
// base: './' makes every asset path relative, so the same build works whether
// it's served from a domain root or a subpath like /test/ (GitHub Pages).
export default defineConfig({
  base: './',
  plugins: [react()],
});
