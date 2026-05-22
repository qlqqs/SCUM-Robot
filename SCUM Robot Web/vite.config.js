import { fileURLToPath, URL } from 'node:url'
import path from 'node:path'
import fs from 'node:fs'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

const BACKEND_PUBLIC_DIR = path.resolve(__dirname, '../SCUM Robot/public')
const PRESERVED_ENTRIES = new Set(['images', '.gitkeep'])

function cleanBackendPublicDir() {
  fs.mkdirSync(BACKEND_PUBLIC_DIR, { recursive: true })

  for (const entry of fs.readdirSync(BACKEND_PUBLIC_DIR, { withFileTypes: true })) {
    if (PRESERVED_ENTRIES.has(entry.name)) {
      continue
    }

    const targetPath = path.join(BACKEND_PUBLIC_DIR, entry.name)
    fs.rmSync(targetPath, { recursive: true, force: true })
  }
}

function customCleanPlugin(enabled) {
  return {
    name: 'custom-clean',
    buildStart() {
      if (!enabled) {
        return
      }
      cleanBackendPublicDir()
    },
  }
}

function normalizeBaseUrl(baseUrl) {
  return baseUrl.replace(/\/+$/, '')
}

function getAssetFileName(assetName) {
  if (/\.(woff|woff2|eot|ttf|otf)$/i.test(assetName)) {
    return 'assets/fonts/[name]-[hash].[ext]'
  }

  if (/\.(png|jpe?g|gif|svg|ico|webp)$/i.test(assetName)) {
    return 'assets/images/[name]-[hash].[ext]'
  }

  return 'assets/[name]-[hash].[ext]'
}

export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiBaseUrl = normalizeBaseUrl(env.VITE_API_BASE_URL || 'http://localhost:8000')
  const shouldCleanBackendPublicDir = command === 'build'

  return {
    base: '/static/',
    plugins: [vue(), vueDevTools(), customCleanPlugin(shouldCleanBackendPublicDir)],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    build: {
      outDir: BACKEND_PUBLIC_DIR,
      emptyOutDir: false,
      assetsDir: 'assets',
      copyPublicDir: true,
      cssCodeSplit: false,
      rollupOptions: {
        output: {
          assetFileNames: (assetInfo) => getAssetFileName(assetInfo.name || ''),
          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
        },
      },
    },
    server: {
      port: 3000,
      open: true,
      proxy: {
        '/static': {
          target: apiBaseUrl,
          changeOrigin: true,
          configure: (proxy) => {
            proxy.on('error', (error) => {
              console.log('静态资源代理错误:', error.message)
            })
          },
        },
      },
    },
  }
})
