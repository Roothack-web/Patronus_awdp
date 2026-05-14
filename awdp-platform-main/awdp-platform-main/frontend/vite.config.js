import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
      '/auth': 'http://localhost:5000',
      '/admin': 'http://localhost:5000',
    },
  },
})
