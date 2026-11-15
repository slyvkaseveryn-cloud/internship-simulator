import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Local dev talks to the deployed stack: config, case files and the API come from CloudFront.
const target = process.env.SITE_URL ?? 'https://d174ecvpoyspb1.cloudfront.net'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target, changeOrigin: true },
      '/config.json': { target, changeOrigin: true },
      '/cases': { target, changeOrigin: true },
    },
  },
})
