
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
     manifest: {
  name: 'AI Trip War Room',
  short_name: 'Trip War Room',
  description: 'Plan and collaborate on trips with AI Trip War Room.',
  theme_color: '#0f172a',
  background_color: '#ffffff',
  display: 'standalone',
  start_url: '/',
  scope: '/',
  icons: [
    {
      src: '/pwa-192x192.png',
      sizes: '192x192',
      type: 'image/png',
    },
    {
      src: '/pwa-512x512.png',
      sizes: '512x512',
      type: 'image/png',
    },
  ],
},
    }),
  ],
})
