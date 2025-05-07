import { fileURLToPath, URL } from 'url';
import { defineConfig, loadEnv } from 'vite'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import eslint from 'vite-plugin-eslint'

export default defineConfig(({ mode }) => {
    import.meta.env = loadEnv(mode, import.meta.dirname);
    return {
        base: import.meta.env.VITE_BASE_URL,
        plugins: [
            vue(),
            eslint({cwd: import.meta.dirname}),
            tailwindcss(),
        ],
        resolve: {
            alias: {
                '@': fileURLToPath(new URL('./src', import.meta.url)),
            },
        },
        server: {
            port: 5173,
        },
    }
})
