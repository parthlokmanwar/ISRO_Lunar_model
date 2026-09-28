import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Backend location is configurable so the dev server can be pointed at a
// different port without editing this file:
//   VITE_PROXY_TARGET=http://localhost:8001 npm run dev
const target = process.env.VITE_PROXY_TARGET || 'http://localhost:8001';
// 5173 rather than 3000: another local app on this machine holds 3000, and with
// strictPort Vite refuses to start instead of silently moving.
const port = Number(process.env.VITE_PORT || 5173);

export default defineConfig({
  plugins: [react()],
  server: {
    port,
    strictPort: true,
    proxy: {
      '/api': { target, changeOrigin: true },
      '/static': { target, changeOrigin: true },
      '/examples': { target, changeOrigin: true },
    },
  },
  build: {
    // three.js dominates the bundle; splitting it keeps the app chunk small.
    rollupOptions: {
      output: {
        manualChunks: {
          three: ['three', '@react-three/fiber', '@react-three/drei'],
          react: ['react', 'react-dom'],
        },
      },
    },
  },
});
