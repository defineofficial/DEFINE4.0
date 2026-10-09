import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://127.0.0.1:8000',
      '/me': 'http://127.0.0.1:8000',
      '/campaigns': 'http://127.0.0.1:8000',
      '/templates': 'http://127.0.0.1:8000',
      '/audience': 'http://127.0.0.1:8000',
      '/contacts': 'http://127.0.0.1:8000',
      '/r': 'http://127.0.0.1:8000',
      '/s': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/webhooks': 'http://127.0.0.1:8000',
    },
  },
})

