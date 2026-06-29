<script setup lang="ts">
import type { Card } from '~/composables/useDecks'

const route = useRoute()
const router = useRouter()
const { getDeck, addCard, updateCard, deleteCard, updateDeck } = useDecks()

const deckId = route.params.id as string
const deck = computed(() => getDeck(deckId))

watchEffect(() => {
  if (!deck.value) router.push('/')
})

// Card form (add + edit)
const isCardFormOpen = ref(false)
const editingCard = ref<Card | null>(null)

const openAddCard = () => {
  editingCard.value = null
  isCardFormOpen.value = true
}

const openEditCard = (card: Card) => {
  editingCard.value = card
  isCardFormOpen.value = true
}

watch(isCardFormOpen, (val) => {
  if (!val) editingCard.value = null
})

const handleCardSubmit = (front: string, back: string) => {
  if (editingCard.value) {
    updateCard(deckId, editingCard.value.id, front, back)
  } else {
    addCard(deckId, front, back)
  }
}

// Card delete
const deletingCardId = ref<string | null>(null)
const isDeleteCardOpen = ref(false)

const openDeleteCard = (id: string) => {
  deletingCardId.value = id
  isDeleteCardOpen.value = true
}

watch(isDeleteCardOpen, (val) => {
  if (!val) deletingCardId.value = null
})

const handleDeleteCard = () => {
  if (deletingCardId.value) {
    deleteCard(deckId, deletingCardId.value)
    isDeleteCardOpen.value = false
  }
}

// Deck edit
const isEditDeckOpen = ref(false)

const handleEditDeck = (name: string, desc: string) => {
  updateDeck(deckId, name, desc)
}
</script>

<template>
  <UContainer
    v-if="deck"
    class="py-10 max-w-5xl"
  >
    <!-- Header -->
    <div
      class="mb-8"
    >
      <UBreadcrumb
        :items="[{ label: 'Decks', to: '/' }, { label: deck.name }]"
        class="mb-4"
      />

      <div
        class="flex flex-wrap items-start justify-between gap-4"
      >
        <div
          class="min-w-0"
        >
          <h1
            class="text-3xl font-bold flex items-center gap-2 flex-wrap"
          >
            {{ deck.name }}
            <UButton
              icon="i-lucide-pencil"
              size="xs"
              color="neutral"
              variant="ghost"
              @click="isEditDeckOpen = true"
            />
          </h1>
          <p
            v-if="deck.description"
            class="text-muted mt-1"
          >
            {{ deck.description }}
          </p>
          <div
            class="flex items-center gap-3 mt-3"
          >
            <UBadge
              :label="`${deck.cards.length} ${deck.cards.length === 1 ? 'card' : 'cards'}`"
              variant="subtle"
              color="neutral"
            />
          </div>
        </div>

        <div
          class="flex gap-2 shrink-0"
        >
          <UButton
            :to="`/study/${deckId}`"
            :disabled="deck.cards.length === 0"
            icon="i-lucide-play"
          >
            Study
          </UButton>
          <UButton
            icon="i-lucide-plus"
            color="neutral"
            variant="subtle"
            @click="openAddCard"
          >
            Add Card
          </UButton>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-show="deck.cards.length === 0"
      class="py-20"
    >
      <UEmpty
        icon="i-lucide-credit-card"
        title="No cards yet"
        description="Add some cards to start studying this deck"
      >
        <template #actions>
          <UButton
            icon="i-lucide-plus"
            @click="openAddCard"
          >
            Add your first card
          </UButton>
        </template>
      </UEmpty>
    </div>

    <!-- Cards list -->
    <div
      v-show="deck.cards.length > 0"
      class="flex flex-col gap-3"
    >
      <UCard
        v-for="(card, index) in deck.cards"
        :key="card.id"
      >
        <div
          class="flex items-start gap-4"
        >
          <span class="text-xs font-mono text-muted pt-0.5 w-5 shrink-0">{{ index + 1 }}</span>
          <div
            class="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4 min-w-0"
          >
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-muted mb-1">Front</p>
              <p class="text-sm whitespace-pre-wrap wrap-break-word">{{ card.front }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-muted mb-1">Back</p>
              <p class="text-sm whitespace-pre-wrap wrap-break-word">{{ card.back }}</p>
            </div>
          </div>
          <div
            class="flex gap-1 shrink-0"
          >
            <UButton
              icon="i-lucide-pencil"
              size="xs"
              color="neutral"
              variant="ghost"
              @click="openEditCard(card)"
            />
            <UButton
              icon="i-lucide-trash-2"
              size="xs"
              color="error"
              variant="ghost"
              @click="openDeleteCard(card.id)"
            />
          </div>
        </div>
      </UCard>
    </div>

    <!-- Modals -->
    <CardFormModal
      v-model:open="isCardFormOpen"
      :card="editingCard"
      @submit="handleCardSubmit"
    />

    <AppConfirmModal
      v-model:open="isDeleteCardOpen"
      title="Delete card?"
      message="This card will be permanently deleted."
      @confirm="handleDeleteCard"
    />

    <DeckFormModal
      v-model:open="isEditDeckOpen"
      :deck="deck"
      @submit="handleEditDeck"
    />
  </UContainer>
</template>
