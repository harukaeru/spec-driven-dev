import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// /api へのリクエストは Python バックエンド (http://localhost:8000) へプロキシする。
// これによりブラウザからは同一オリジンとして扱われ、CORS を気にせず開発できる。
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
