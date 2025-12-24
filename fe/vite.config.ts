import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import Unocss from 'unocss/vite'
import { defineConfig } from 'vite'
import vueDevTools from 'vite-plugin-vue-devtools'

const baseSrc = fileURLToPath(new URL('./src', import.meta.url))
// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueJsx(), vueDevTools(), Unocss()],
  server: { port: 5100, host: true },
  resolve: {
    alias: [
      {
        find: '@',
        replacement: baseSrc,
      },
    ],
  },
})
