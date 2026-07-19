<script setup lang="ts">
import type { Deck } from '~/composables/useDecks'

defineProps<{
  deck: Deck
}>()
</script>

<template>
  <UCard
    class="group hover:shadow-md transition-shadow"
  >
    <div
      class="flex flex-col gap-3 h-full"
    >
      <div
        class="flex-1"
      >
        <div class="flex items-start gap-2">
          <h3
            class="font-semibold text-lg leading-tight flex-1"
          >
            {{ deck.name }}
          </h3>
          <UBadge
            v-if="deck.isPinned"
            label="Pinned"
            variant="subtle"
            color="primary"
            size="xs"
            class="shrink-0"
          />
        </div>
        <p
          v-if="deck.ownerUsername"
          class="text-xs text-muted mt-1"
        >
          by {{ deck.ownerUsername }}
        </p>
        <p
          v-if="deck.description"
          class="text-sm text-muted mt-1 line-clamp-2"
        >
          {{ deck.description }}
        </p>
      </div>

      <div
        class="flex items-center gap-2 flex-wrap"
      >
        <UBadge
          :label="`${deck.cards.length} ${deck.cards.length === 1 ? 'card' : 'cards'}`"
          variant="subtle"
          color="neutral"
          size="sm"
        />
        <UBadge
          v-if="deck.saveCount !== undefined && deck.saveCount > 0"
          :label="`Saved ${deck.saveCount} ${deck.saveCount === 1 ? 'time' : 'times'}`"
          variant="subtle"
          color="neutral"
          size="sm"
        />
      </div>

      <div
        class="flex gap-2 pt-1"
      >
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
          :icon="deck.isPinned ? 'i-lucide-eye' : 'i-lucide-settings-2'"
          size="sm"
          color="neutral"
          variant="subtle"
        >
          {{ deck.isPinned ? 'View' : 'Manage' }}
        </UButton>
      </div>
    </div>
  </UCard>
</template>
