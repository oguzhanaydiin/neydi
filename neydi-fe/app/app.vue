<script setup>
import { CUSTOM_THEMES } from '~/composables/useTheme'

const { theme, setTheme } = useTheme()
const { isLoggedIn, user, logout, restoreSession } = useAuth()

useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: computed(() => ({
    lang: 'en',
    ...(CUSTOM_THEMES.includes(theme.value) ? { 'data-theme': theme.value } : {})
  }))
})

useSeoMeta({
  title: 'neydi - flashcards',
  description: 'A simple flashcard app to help you remember things.'
})

onMounted(() => {
  setTheme(theme.value)
  restoreSession()
})
</script>

<template>
  <UApp>
    <UHeader :toggle="false">
      <template #left>
        <NuxtLink
          to="/"
          class="font-bold text-xl tracking-tight text-primary"
        >
          neydi
        </NuxtLink>
      </template>

      <template #right>
        <div class="flex items-center gap-2">
          <template v-if="isLoggedIn">
            <span class="text-sm text-muted hidden sm:inline">{{ user?.username }}</span>
            <UButton
              variant="ghost"
              size="sm"
              icon="i-lucide-log-out"
              @click="logout"
            >
              <span class="hidden sm:inline">Sign out</span>
            </UButton>
          </template>
          <template v-else>
            <UButton
              to="/login"
              variant="outline"
              size="sm"
              class="px-3 py-1.5 text-sm"
            >
              Sign in
            </UButton>
          </template>
          <ThemeSwitcher />
        </div>
      </template>
    </UHeader>

    <UMain>
      <NuxtPage />
    </UMain>

    <UFooter>
      <template #left>
        <p
          class="text-sm text-muted"
        >
          neydi - remember more, forget less
        </p>
      </template>
    </UFooter>
  </UApp>
</template>
