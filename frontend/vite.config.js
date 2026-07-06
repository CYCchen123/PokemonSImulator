import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const API_HOST = process.env.VITE_API_HOST || 'http://192.168.209.137:8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: API_HOST, changeOrigin: true },
      '/ws': { target: API_HOST.replace('http', 'ws'), ws: true, changeOrigin: true },
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  }
})
