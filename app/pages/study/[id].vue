<script setup lang="ts">
import type { Card } from '~/composables/useDecks'

const route = useRoute()
const router = useRouter()
const { getDeck } = useDecks()

const deckId = route.params.id as string
const deck = computed(() => getDeck(deckId))

watchEffect(() => {
  if (!deck.value) router.push('/')
})

// Session state
const queue = ref<Card[]>([])
const revealed = ref(false)
const done = ref(false)
const gotItCount = ref(0)
const totalCards = ref(0)

const currentCard = computed(() => queue.value[0])
const progress = computed(() =>
  totalCards.value === 0 ? 0 : Math.round((gotItCount.value / totalCards.value) * 100)
)

const initSession = () => {
  if (!deck.value) return
  queue.value = [...deck.value.cards].sort(() => Math.random() - 0.5)
  totalCards.value = queue.value.length
  gotItCount.value = 0
  revealed.value = false
  done.value = false
}

onMounted(initSession)

const reveal = () => {
  revealed.value = true
}

const again = () => {
  const card = queue.value.shift()!
  queue.value.push(card)
  revealed.value = false
}

const gotIt = () => {
  queue.value.shift()
  gotItCount.value++
  revealed.value = false
  if (queue.value.length === 0) {
    done.value = true
  }
}

const restart = () => {
  initSession()
}
</script>

<template>
  <UContainer
    v-if="deck"
    class="py-10 max-w-2xl"
  >
    <!-- Header -->
    <div
      class="flex items-center justify-between gap-2 mb-6"
    >
      <div
        class="min-w-0 flex-1"
      >
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
    <div
      class="mb-6"
    >
      <div
        class="flex justify-between text-sm text-muted mb-2"
      >
        <span>{{ gotItCount }} / {{ totalCards }} cards learned</span>
        <span>{{ queue.length }} remaining</span>
      </div>
      <UProgress :model-value="progress" />
    </div>

    <!-- Done state -->
    <div
      v-if="done"
      class="py-12 text-center"
    >
      <div class="text-6xl mb-4">🎉</div>
      <h2 class="text-2xl font-bold mb-2">Session complete!</h2>
      <p
        class="text-muted mb-8"
      >
        You went through all {{ totalCards }} cards in <strong>{{ deck.name }}</strong>.
      </p>
      <div
        class="flex justify-center gap-3"
      >
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
          icon="i-lucide-settings-2"
        >
          Manage deck
        </UButton>
      </div>
    </div>

    <!-- Study card -->
    <template v-else-if="currentCard">
      <FlashCard
        :front="currentCard.front"
        :back="currentCard.back"
        :revealed="revealed"
        @reveal="reveal"
      />

      <div
        class="mt-6 flex flex-col items-center gap-3"
      >
        <template v-if="!revealed">
          <UButton
            size="xl"
            class="w-full max-w-sm"
            icon="i-lucide-eye"
            @click="reveal"
          >
            Reveal Answer
          </UButton>
        </template>
        <template v-else>
          <p class="text-sm text-muted">How did you do?</p>
          <div
            class="flex gap-3 w-full max-w-sm"
          >
            <UButton
              size="xl"
              color="error"
              variant="subtle"
              class="flex-1"
              icon="i-lucide-rotate-ccw"
              @click="again"
            >
              Again
            </UButton>
            <UButton
              size="xl"
              color="success"
              class="flex-1"
              icon="i-lucide-check"
              @click="gotIt"
            >
              Got it
            </UButton>
          </div>
        </template>
      </div>

      <!-- Card counter -->
      <p
        class="text-center text-xs text-muted mt-6"
      >
        Card {{ gotItCount + 1 }} of {{ totalCards }}
        <span
          v-if="queue.length > totalCards - gotItCount"
          class="ml-1 text-warning"
        >(repeating)</span>
      </p>
    </template>
  </UContainer>
</template>
