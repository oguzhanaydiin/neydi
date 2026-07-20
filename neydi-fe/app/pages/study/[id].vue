<script setup lang="ts">
import type { Card } from '~/composables/useDecks'

const route = useRoute()
const router = useRouter()
const { getDeck, isOwnedDeck, decksReady, updateCardConfidence } = useDecks()

const flashCardRef = ref<{ swipeOut: (d: 'left' | 'right') => void } | null>(null)

const deckId = route.params.id as string
const deck = computed(() => getDeck(deckId))
const isOwned = computed(() => isOwnedDeck(deckId))

watchEffect(() => {
  if (decksReady.value && !deck.value) router.push('/')
})

interface SessionCard extends Card {
  sessionConfidence: number
}

const queue = ref<SessionCard[]>([])
const revealed = ref(false)
const done = ref(false)
const knownCount = ref(0)
const unknownCount = ref(0)
const totalCards = ref(0)

const currentCard = computed(() => queue.value[0])
const answeredCount = computed(() => knownCount.value + unknownCount.value)
const progress = computed(() =>
  totalCards.value === 0 ? 0 : Math.round((answeredCount.value / totalCards.value) * 100)
)

const improvedCount = computed(() => {
  if (!deck.value) return 0
  return deck.value.cards.filter(c => (c.confidence ?? 0) > 0).length
})

const initSession = () => {
  if (!deck.value) return
  const sorted = [...deck.value.cards].sort((a, b) => {
    const diff = (a.confidence ?? 0) - (b.confidence ?? 0)
    return diff !== 0 ? diff : Math.random() - 0.5
  })
  queue.value = sorted.map(c => ({ ...c, sessionConfidence: c.confidence ?? 0 }))
  totalCards.value = sorted.length
  knownCount.value = 0
  unknownCount.value = 0
  revealed.value = false
  done.value = false
}

watch(deck, (d) => {
  if (d) initSession()
}, { immediate: true })

const toggleReveal = () => {
  revealed.value = !revealed.value
}

// know +1, dontKnow -2 (forgetting penalised more than remembering)
const know = () => {
  const card = queue.value.shift()!
  updateCardConfidence(deckId, card.id, Math.min(5, (card.confidence ?? 0) + 1))
  knownCount.value++
  revealed.value = false
  if (queue.value.length === 0) done.value = true
}

const dontKnow = () => {
  const card = queue.value.shift()!
  updateCardConfidence(deckId, card.id, Math.max(0, (card.confidence ?? 0) - 2))
  unknownCount.value++
  revealed.value = false
  if (queue.value.length === 0) done.value = true
}

const handleKnow = () => flashCardRef.value?.swipeOut('right')
const handleDontKnow = () => flashCardRef.value?.swipeOut('left')

const restart = () => {
  initSession()
}

const confidenceLabelFor = (c: number) => {
  if (c === 0) return 'New'
  if (c === 1) return 'Seen'
  if (c === 2) return 'Learning'
  if (c === 3) return 'Familiar'
  if (c === 4) return 'Strong'
  return 'Mastered'
}
</script>

<template>
  <div
    v-if="!decksReady"
    class="py-24 flex justify-center"
  >
    <UIcon
      name="i-lucide-loader-circle"
      class="animate-spin size-8 text-muted"
    />
  </div>

  <UContainer
    v-else-if="deck"
    class="py-10 max-w-2xl"
  >
    <!-- Header -->
    <div class="flex items-center justify-between gap-2 mb-6">
      <div class="min-w-0 flex-1">
        <UBreadcrumb
          :items="[{ label: 'Decks', to: '/' }, { label: deck.name, to: `/decks/${deckId}` }, { label: 'Study' }]"
        />
      </div>
      <UButton
        :to="`/decks/${deckId}`"
        icon="i-lucide-x"
        color="neutral"
        variant="ghost"
        size="sm"
        class="shrink-0"
      />
    </div>

    <!-- Progress -->
    <div class="mb-6">
      <div class="flex justify-between text-sm text-muted mb-2">
        <span class="flex items-center gap-3">
          <span class="flex items-center gap-1 text-success">
            <UIcon
              name="i-lucide-check"
              class="size-3.5"
            />
            {{ knownCount }} known
          </span>
          <span
            v-if="unknownCount > 0"
            class="flex items-center gap-1 text-error"
          >
            <UIcon
              name="i-lucide-rotate-ccw"
              class="size-3.5"
            />
            {{ unknownCount }} again
          </span>
        </span>
        <span>{{ queue.length }} remaining</span>
      </div>
      <UProgress
        :model-value="progress"
        color="success"
      />
    </div>

    <!-- Done state -->
    <div
      v-if="done"
      class="py-12 text-center"
    >
      <div class="text-6xl mb-4">🎉</div>
      <h2 class="text-2xl font-bold mb-2">Session complete!</h2>
      <p class="text-muted mb-6">
        You went through all {{ totalCards }} cards in <strong>{{ deck.name }}</strong>.
      </p>

      <div class="flex justify-center gap-4 mb-8">
        <div class="rounded-xl border border-default bg-elevated px-6 py-4 text-center">
          <p class="text-2xl font-bold text-success">{{ knownCount }}</p>
          <p class="text-xs text-muted mt-1">Known</p>
        </div>
        <div class="rounded-xl border border-default bg-elevated px-6 py-4 text-center">
          <p class="text-2xl font-bold text-error">{{ unknownCount }}</p>
          <p class="text-xs text-muted mt-1">Didn't Know</p>
        </div>
        <div class="rounded-xl border border-default bg-elevated px-6 py-4 text-center">
          <p class="text-2xl font-bold text-primary">{{ improvedCount }}</p>
          <p class="text-xs text-muted mt-1">With Confidence</p>
        </div>
      </div>

      <div class="flex justify-center gap-3">
        <UButton
          icon="i-lucide-rotate-ccw"
          color="neutral"
          variant="subtle"
          @click="restart"
        >
          Study again
        </UButton>
        <UButton
          :to="`/decks/${deckId}`"
          :icon="isOwned ? 'i-lucide-settings-2' : 'i-lucide-eye'"
        >
          {{ isOwned ? 'Manage deck' : 'View deck' }}
        </UButton>
      </div>
    </div>

    <!-- Study card -->
    <template v-else-if="currentCard">
      <FlashCard
        :key="currentCard.id"
        ref="flashCardRef"
        :front="currentCard.front"
        :back="currentCard.back"
        :revealed="revealed"
        :confidence="currentCard.confidence"
        @toggle="toggleReveal"
        @known="know"
        @unknown="dontKnow"
      />

      <p class="text-center text-xs text-muted mt-3">
        {{ confidenceLabelFor(currentCard.confidence ?? 0) }}
        <span class="opacity-40">({{ currentCard.confidence ?? 0 }}/5)</span>
      </p>

      <div class="mt-4 flex flex-col items-center gap-3">
        <p class="text-sm text-muted">Did you know it?</p>
        <div class="flex gap-3 w-full max-w-sm">
          <div class="flex-1 flex flex-col items-center gap-1">
            <UButton
              size="xl"
              color="error"
              variant="subtle"
              class="w-full"
              icon="i-lucide-x"
              @click="handleDontKnow"
            >
              Don't Know
            </UButton>
            <span class="text-xs text-error/60">
              → {{ confidenceLabelFor(Math.max(0, (currentCard.confidence ?? 0) - 2)) }}
            </span>
          </div>
          <div class="flex-1 flex flex-col items-center gap-1">
            <UButton
              size="xl"
              color="success"
              class="w-full"
              icon="i-lucide-check"
              @click="handleKnow"
            >
              Know
            </UButton>
            <span class="text-xs text-success/60">
              → {{ confidenceLabelFor(Math.min(5, (currentCard.confidence ?? 0) + 1)) }}
            </span>
          </div>
        </div>
      </div>

      <p class="text-center text-xs text-muted mt-6">
        Card {{ answeredCount + 1 }} of {{ totalCards }}
      </p>
    </template>
  </UContainer>
</template>
