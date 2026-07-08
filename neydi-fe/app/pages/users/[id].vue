<script setup lang="ts">
const route = useRoute()
const { public: { apiBase } } = useRuntimeConfig()

interface UserInfo {
  id: string
  username: string
  created_at: string
}

interface Card {
  id: string
  front: string
  back: string
  confidence: number
}

interface Deck {
  id: string
  name: string
  description?: string
  cards: Card[]
  createdAt: number
}

const userId = route.params.id as string
const user = ref<UserInfo | null>(null)
const decks = ref<Deck[]>([])
const loading = ref(true)
const expandedDecks = ref<Set<string>>(new Set())

const toggleDeck = (deckId: string) => {
  const next = new Set(expandedDecks.value)
  if (next.has(deckId)) {
    next.delete(deckId)
  } else {
    next.add(deckId)
  }
  expandedDecks.value = next
}

onMounted(async () => {
  try {
    const [userRes, decksRes] = await Promise.all([
      $fetch<UserInfo>(`${apiBase}/users/${userId}`),
      $fetch<Deck[]>(`${apiBase}/users/${userId}/decks`)
    ])
    user.value = userRes
    decks.value = decksRes
  } catch {
    navigateTo('/users')
  } finally {
    loading.value = false
  }
})

const totalCards = computed(() => decks.value.reduce((acc, d) => acc + d.cards.length, 0))

const formatDate = (dateStr: string) =>
  new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })

const confidenceDotClass = (card: Card, i: number) => {
  if (i > (card.confidence ?? 0)) return 'bg-muted/30'
  const c = card.confidence ?? 0
  if (c <= 2) return 'bg-error'
  if (c === 3) return 'bg-warning'
  if (c === 4) return 'bg-info'
  return 'bg-success'
}
</script>

<template>
  <UContainer class="py-10">
    <!-- Loading -->
    <div
      v-if="loading"
      class="py-24 flex justify-center"
    >
      <UIcon
        name="i-lucide-loader-circle"
        class="animate-spin size-8 text-muted"
      />
    </div>

    <template v-else-if="user">
      <!-- Breadcrumb -->
      <UBreadcrumb
        :items="[{ label: 'Users', to: '/users' }, { label: user.username }]"
        class="mb-6"
      />

      <!-- User Header -->
      <div class="flex flex-wrap items-center gap-4 mb-8">
        <div class="bg-primary/10 rounded-full p-4 shrink-0">
          <UIcon
            name="i-lucide-user"
            class="size-8 text-primary"
          />
        </div>
        <div>
          <h1 class="text-3xl font-bold">
            {{ user.username }}
          </h1>
          <p class="text-muted mt-0.5 text-sm">
            Joined {{ formatDate(user.created_at) }}
          </p>
        </div>
        <div class="flex gap-3 ml-0 sm:ml-auto">
          <div class="text-center">
            <p class="text-2xl font-bold text-primary">
              {{ decks.length }}
            </p>
            <p class="text-xs text-muted">
              {{ decks.length === 1 ? 'Deck' : 'Decks' }}
            </p>
          </div>
          <div class="text-center">
            <p class="text-2xl font-bold text-primary">
              {{ totalCards }}
            </p>
            <p class="text-xs text-muted">
              Cards
            </p>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-if="decks.length === 0"
        class="py-20"
      >
        <UEmpty
          icon="i-lucide-layers"
          title="No decks yet"
          :description="`${user.username} hasn't created any decks yet`"
        />
      </div>

      <!-- Decks -->
      <div
        v-else
        class="flex flex-col gap-4"
      >
        <p class="text-sm text-muted mb-2">
          {{ decks.length }} {{ decks.length === 1 ? 'deck' : 'decks' }} · {{ totalCards }} {{ totalCards === 1 ? 'card' : 'cards' }}
        </p>

        <div
          v-for="deck in decks"
          :key="deck.id"
        >
          <UCard>
            <!-- Deck header (clickable to expand) -->
            <div
              class="flex items-center gap-3 cursor-pointer select-none"
              @click="toggleDeck(deck.id)"
            >
              <div class="flex-1 min-w-0">
                <h3 class="font-semibold text-lg leading-tight">
                  {{ deck.name }}
                </h3>
                <p
                  v-if="deck.description"
                  class="text-sm text-muted mt-0.5 line-clamp-1"
                >
                  {{ deck.description }}
                </p>
              </div>

              <div class="flex items-center gap-3 shrink-0">
                <UBadge
                  :label="`${deck.cards.length} ${deck.cards.length === 1 ? 'card' : 'cards'}`"
                  variant="subtle"
                  color="neutral"
                  size="sm"
                />
                <UIcon
                  :name="expandedDecks.has(deck.id) ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
                  class="size-4 text-muted transition-transform"
                />
              </div>
            </div>

            <!-- Cards (expanded) -->
            <div
              v-if="expandedDecks.has(deck.id)"
              class="mt-4 border-t pt-4 flex flex-col gap-3"
            >
              <div
                v-if="deck.cards.length === 0"
                class="py-6 text-center text-muted text-sm"
              >
                No cards in this deck yet
              </div>

              <div
                v-for="(card, index) in deck.cards"
                :key="card.id"
                class="flex items-start gap-3"
              >
                <span class="text-sm font-mono text-muted w-6 text-right shrink-0 pt-0.5">
                  {{ index + 1 }}
                </span>
                <div class="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-3 min-w-0">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-wide text-muted mb-1">
                      Front
                    </p>
                    <p class="text-sm whitespace-pre-wrap wrap-break-word">
                      {{ card.front }}
                    </p>
                  </div>
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-wide text-muted mb-1">
                      Back
                    </p>
                    <p class="text-sm whitespace-pre-wrap wrap-break-word">
                      {{ card.back }}
                    </p>
                  </div>
                </div>
                <!-- Confidence dots (read-only) -->
                <div class="hidden sm:flex items-center gap-1 shrink-0 pt-1">
                  <div
                    v-for="i in 5"
                    :key="i"
                    class="w-1.5 h-1.5 rounded-full"
                    :class="confidenceDotClass(card, i)"
                  />
                </div>
              </div>
            </div>
          </UCard>
        </div>
      </div>
    </template>
  </UContainer>
</template>
