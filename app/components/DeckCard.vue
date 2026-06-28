<script setup lang="ts">
import type { Deck } from '~/composables/useDecks'

defineProps<{
  deck: Deck
}>()
</script>

<template>
  <UCard class="group hover:shadow-md transition-shadow">
    <div class="flex flex-col gap-3 h-full">
      <div class="flex-1">
        <h3 class="font-semibold text-lg leading-tight">{{ deck.name }}</h3>
        <p v-if="deck.description" class="text-sm text-muted mt-1 line-clamp-2">
          {{ deck.description }}
        </p>
      </div>

      <div class="flex items-center gap-2">
        <UBadge
          :label="`${deck.cards.length} ${deck.cards.length === 1 ? 'card' : 'cards'}`"
          variant="subtle"
          color="neutral"
          size="sm"
        />
      </div>

      <div class="flex gap-2 pt-1">
        <UButton
          :to="`/study/${deck.id}`"
          :disabled="deck.cards.length === 0"
          icon="i-lucide-play"
          size="sm"
          class="flex-1"
        >
          Study
        </UButton>
        <UButton
          :to="`/decks/${deck.id}`"
          icon="i-lucide-settings-2"
          size="sm"
          color="neutral"
          variant="subtle"
        >
          Manage
        </UButton>
      </div>
    </div>
  </UCard>
</template>
