import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:9000', changeOrigin: true },
      '/ws': { target: 'http://localhost:9000', ws: true, changeOrigin: true },
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  }
})
