// https://nuxt.com/docs/api/configuration/nuxt-config
const apiProxyTarget = process.env.NUXT_API_PROXY_TARGET || 'http://127.0.0.1:8000'

export default defineNuxtConfig({
  modules: [
    '@nuxt/eslint',
    '@nuxt/ui'
  ],

  devtools: {
    enabled: true
  },

  css: ['~/assets/css/main.css'],

  colorMode: {
    preference: 'dark',
    fallback: 'dark'
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api'
    }
  },

  routeRules: {
    '/api/**': { proxy: `${apiProxyTarget}/**` }
  },

  sourcemap: {
    server: false,
    client: false
  },

  compatibilityDate: '2025-01-15',

  nitro: {
    devProxy: {
      '/api/': {
        target: `${apiProxyTarget}/`,
        changeOrigin: true
      }
    }
  },

  vite: {
    build: {
      sourcemap: false,
      modulePreload: false,
      chunkSizeWarningLimit: 600,
      rollupOptions: {
        onwarn(warning, defaultHandler) {
          if (warning.message?.includes('/* #__PURE__ */')) {
            return
          }

          defaultHandler(warning)
        }
      }
    }
  },

  eslint: {
    config: {
      stylistic: {
        commaDangle: 'never',
        braceStyle: '1tbs'
      }
    }
  },

  icon: {
    localApiEndpoint: '/_nuxt_icon'
  }
})
