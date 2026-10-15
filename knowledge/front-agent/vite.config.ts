import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  base: mode === 'production' ? '/agent/' : '/',
  server: {
    port: 5173,
    proxy: {
      '/query': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/stream': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/history': { target: 'http://127.0.0.1:8001', changeOrigin: true },
      '/status': { target: 'http://127.0.0.1:8001', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
}))
