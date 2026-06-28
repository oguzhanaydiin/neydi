<script setup>
useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: 'en'
  }
})

useSeoMeta({
  title: 'neydi — flashcards',
  description: 'A simple flashcard app to help you remember things.'
})
</script>

<template>
  <UApp>
    <UHeader>
      <template #left>
        <NuxtLink to="/" class="font-bold text-xl tracking-tight text-primary">
          neydi
        </NuxtLink>
      </template>

      <template #right>
        <UColorModeButton />
      </template>
    </UHeader>

    <UMain>
      <NuxtPage />
    </UMain>

    <UFooter>
      <template #left>
        <p class="text-sm text-muted">
          neydi — remember more, forget less
        </p>
      </template>
    </UFooter>
  </UApp>
</template>
