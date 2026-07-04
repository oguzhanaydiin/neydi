<script setup lang="ts">
import type { Card } from '~/composables/useDecks'

const route = useRoute()
const router = useRouter()
const { getDeck, addCard, updateCard, deleteCard, updateDeck, reorderCards } = useDecks()

const deckId = route.params.id as string
const deck = computed(() => getDeck(deckId))

watchEffect(() => {
  if (!deck.value) router.push('/')
})

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

const handleCardSubmit = async (front: string, back: string) => {
  if (editingCard.value) {
    await updateCard(deckId, editingCard.value.id, front, back)
  } else {
    await addCard(deckId, front, back)
  }
}

const deletingCardId = ref<string | null>(null)
const isDeleteCardOpen = ref(false)

const openDeleteCard = (id: string) => {
  deletingCardId.value = id
  isDeleteCardOpen.value = true
}

watch(isDeleteCardOpen, (val) => {
  if (!val) deletingCardId.value = null
})

const handleDeleteCard = async () => {
  if (deletingCardId.value) {
    await deleteCard(deckId, deletingCardId.value)
    isDeleteCardOpen.value = false
  }
}

const sortOptions = [
  { label: 'My order', value: 'default' },
  { label: 'Front A → Z', value: 'front-asc' },
  { label: 'Front Z → A', value: 'front-desc' },
  { label: 'Confidence: low first', value: 'confidence-asc' },
  { label: 'Confidence: high first', value: 'confidence-desc' }
]
const sortBy = ref('default')

const isDraggable = computed(() => sortBy.value === 'default')

const sortedCards = computed(() => {
  if (!deck.value) return []
  const cards = [...deck.value.cards]
  if (sortBy.value === 'front-asc') return cards.sort((a, b) => a.front.localeCompare(b.front))
  if (sortBy.value === 'front-desc') return cards.sort((a, b) => b.front.localeCompare(a.front))
  if (sortBy.value === 'confidence-asc') return cards.sort((a, b) => (a.confidence ?? 0) - (b.confidence ?? 0))
  if (sortBy.value === 'confidence-desc') return cards.sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))
  return cards
})

const draggableCards = computed(() => deck.value?.cards ?? [])

const isEditDeckOpen = ref(false)

const handleEditDeck = async (name: string, desc: string) => {
  await updateDeck(deckId, name, desc)
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
              @click="() => { isEditDeckOpen = true }"
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
      <div class="flex items-center justify-between mb-1">
        <p class="text-sm text-muted">
          {{ deck.cards.length }} {{ deck.cards.length === 1 ? 'card' : 'cards' }}
        </p>
        <USelect
          v-model="sortBy"
          :items="sortOptions"
          value-key="value"
          label-key="label"
          size="xs"
          color="neutral"
          variant="subtle"
          icon="i-lucide-arrow-up-down"
          class="w-48"
        />
      </div>

      <DraggableList
        v-if="isDraggable"
        :items="draggableCards"
        class="flex flex-col gap-3"
        @reorder="reorderCards(deckId, $event)"
      >
        <template #default="{ item, index, gripListeners }">
          <UCard>
            <CardRow
              :card="item"
              :index="index"
              draggable
              :grip-listeners="gripListeners"
              @edit="openEditCard(item)"
              @delete="openDeleteCard(item.id)"
            />
          </UCard>
        </template>
      </DraggableList>

      <template v-else>
        <UCard
          v-for="card in sortedCards"
          :key="card.id"
        >
          <CardRow
            :card="card"
            :index="deck.cards.findIndex(c => c.id === card.id)"
            @edit="openEditCard(card)"
            @delete="openDeleteCard(card.id)"
          />
        </UCard>
      </template>
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
