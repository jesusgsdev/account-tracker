import { execSync } from 'node:child_process'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import pkg from './package.json' with { type: 'json' }

function resolveAppVersion(): string {
  const envVer = process.env.VITE_APP_VERSION?.trim()
  if (envVer && envVer !== 'latest' && envVer !== 'dev' && envVer !== 'main') {
    return envVer.startsWith('v') ? envVer : `v${envVer}`
  }
  try {
    const tag = execSync('git describe --tags --abbrev=0', {
      stdio: ['ignore', 'pipe', 'ignore'],
    })
      .toString()
      .trim()
    if (tag) return tag.startsWith('v') ? tag : `v${tag}`
  } catch {
    // Fallback to package.json version when building outside a git checkout
  }
  return `v${pkg.version}`
}

export default defineConfig({
  plugins: [vue()],
  define: {
    __APP_VERSION__: JSON.stringify(resolveAppVersion()),
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
