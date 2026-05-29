import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Self-contained SPA build. No backend, no env config required.
export default defineConfig({
  plugins: [react()],
});
