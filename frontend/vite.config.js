import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            '/pipeline': 'http://localhost:8000',
            '/data': 'http://localhost:8000',
            '/quarantine': 'http://localhost:8000',
            '/notifications': 'http://localhost:8000',
            '/ws': {
                target: 'ws://localhost:8000',
                ws: true,
            },
        },
    },
})
