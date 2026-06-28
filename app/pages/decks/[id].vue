<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const { getDeck, addCard, updateCard, deleteCard, updateDeck } = useDecks()

const deckId = route.params.id as string
const deck = computed(() => getDeck(deckId))

watchEffect(() => {
  if (!deck.value) router.push('/')
})

// Add card
const isAddOpen = ref(false)
const newFront = ref('')
const newBack = ref('')
const addErrors = ref({ front: '', back: '' })

const openAdd = () => {
  newFront.value = ''
  newBack.value = ''
  addErrors.value = { front: '', back: '' }
  isAddOpen.value = true
}

const submitAdd = () => {
  addErrors.value = { front: '', back: '' }
  let valid = true
  if (!newFront.value.trim()) { addErrors.value.front = 'Required'; valid = false }
  if (!newBack.value.trim()) { addErrors.value.back = 'Required'; valid = false }
  if (!valid) return
  addCard(deckId, newFront.value, newBack.value)
  isAddOpen.value = false
}

// Edit card
const editCardId = ref<string | null>(null)
const editFront = ref('')
const editBack = ref('')
const editErrors = ref({ front: '', back: '' })

const openEdit = (card: { id: string; front: string; back: string }) => {
  editCardId.value = card.id
  editFront.value = card.front
  editBack.value = card.back
  editErrors.value = { front: '', back: '' }
}

const submitEdit = () => {
  editErrors.value = { front: '', back: '' }
  let valid = true
  if (!editFront.value.trim()) { editErrors.value.front = 'Required'; valid = false }
  if (!editBack.value.trim()) { editErrors.value.back = 'Required'; valid = false }
  if (!valid || !editCardId.value) return
  updateCard(deckId, editCardId.value, editFront.value, editBack.value)
  editCardId.value = null
}

// Delete card
const deleteCardId = ref<string | null>(null)

const doDeleteCard = () => {
  if (deleteCardId.value) {
    deleteCard(deckId, deleteCardId.value)
    deleteCardId.value = null
  }
}

// Edit deck name
const isEditDeckOpen = ref(false)
const editDeckName = ref('')
const editDeckDesc = ref('')
const editDeckError = ref('')

const openEditDeck = () => {
  editDeckName.value = deck.value?.name ?? ''
  editDeckDesc.value = deck.value?.description ?? ''
  editDeckError.value = ''
  isEditDeckOpen.value = true
}

const submitEditDeck = () => {
  if (!editDeckName.value.trim()) {
    editDeckError.value = 'Name is required'
    return
  }
  updateDeck(deckId, editDeckName.value, editDeckDesc.value)
  isEditDeckOpen.value = false
}
</script>

<template>
  <UContainer v-if="deck" class="py-10">
    <!-- Header -->
    <div class="mb-8">
      <UBreadcrumb
        :items="[{ label: 'Decks', to: '/' }, { label: deck.name }]"
        class="mb-4"
      />

      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold flex items-center gap-2">
            {{ deck.name }}
            <UButton
              icon="i-lucide-pencil"
              size="xs"
              color="neutral"
              variant="ghost"
              @click="openEditDeck"
            />
          </h1>
          <p v-if="deck.description" class="text-muted mt-1">{{ deck.description }}</p>
          <div class="flex items-center gap-3 mt-3">
            <UBadge
              :label="`${deck.cards.length} ${deck.cards.length === 1 ? 'card' : 'cards'}`"
              variant="subtle"
              color="neutral"
            />
          </div>
        </div>

        <div class="flex gap-2 shrink-0">
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
            @click="openAdd"
          >
            Add Card
          </UButton>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="deck.cards.length === 0" class="py-20">
      <UEmpty
        icon="i-lucide-credit-card"
        title="No cards yet"
        description="Add some cards to start studying this deck"
      >
        <template #actions>
          <UButton icon="i-lucide-plus" @click="openAdd">
            Add your first card
          </UButton>
        </template>
      </UEmpty>
    </div>

    <!-- Cards list -->
    <div v-else class="flex flex-col gap-3">
      <UCard
        v-for="(card, index) in deck.cards"
        :key="card.id"
      >
        <div class="flex items-start gap-4">
          <span class="text-xs font-mono text-muted pt-0.5 w-5 shrink-0">{{ index + 1 }}</span>
          <div class="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4 min-w-0">
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-muted mb-1">Front</p>
              <p class="text-sm whitespace-pre-wrap break-words">{{ card.front }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold uppercase tracking-wide text-muted mb-1">Back</p>
              <p class="text-sm whitespace-pre-wrap break-words">{{ card.back }}</p>
            </div>
          </div>
          <div class="flex gap-1 shrink-0">
            <UButton
              icon="i-lucide-pencil"
              size="xs"
              color="neutral"
              variant="ghost"
              @click="openEdit(card)"
            />
            <UButton
              icon="i-lucide-trash-2"
              size="xs"
              color="error"
              variant="ghost"
              @click="deleteCardId = card.id"
            />
          </div>
        </div>
      </UCard>
    </div>

    <!-- Add Card Modal -->
    <UModal v-model:open="isAddOpen" title="Add Card">
      <template #body>
        <div class="flex flex-col gap-4">
          <UFormField label="Front" :error="addErrors.front || undefined">
            <UTextarea
              v-model="newFront"
              placeholder="Question or term"
              class="w-full"
              :rows="3"
              autofocus
            />
          </UFormField>
          <UFormField label="Back" :error="addErrors.back || undefined">
            <UTextarea
              v-model="newBack"
              placeholder="Answer or definition"
              class="w-full"
              :rows="3"
            />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton color="neutral" variant="subtle" @click="isAddOpen = false">
            Cancel
          </UButton>
          <UButton icon="i-lucide-plus" @click="submitAdd">
            Add Card
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- Edit Card Modal -->
    <UModal
      :open="!!editCardId"
      title="Edit Card"
      @update:open="editCardId = null"
    >
      <template #body>
        <div class="flex flex-col gap-4">
          <UFormField label="Front" :error="editErrors.front || undefined">
            <UTextarea
              v-model="editFront"
              placeholder="Question or term"
              class="w-full"
              :rows="3"
            />
          </UFormField>
          <UFormField label="Back" :error="editErrors.back || undefined">
            <UTextarea
              v-model="editBack"
              placeholder="Answer or definition"
              class="w-full"
              :rows="3"
            />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton color="neutral" variant="subtle" @click="editCardId = null">
            Cancel
          </UButton>
          <UButton icon="i-lucide-check" @click="submitEdit">
            Save
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- Delete Card Confirmation -->
    <UModal
      :open="!!deleteCardId"
      title="Delete card?"
      @update:open="deleteCardId = null"
    >
      <template #body>
        <p class="text-muted">This card will be permanently deleted.</p>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton color="neutral" variant="subtle" @click="deleteCardId = null">
            Cancel
          </UButton>
          <UButton color="error" icon="i-lucide-trash-2" @click="doDeleteCard">
            Delete
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- Edit Deck Modal -->
    <UModal v-model:open="isEditDeckOpen" title="Edit Deck">
      <template #body>
        <div class="flex flex-col gap-4">
          <UFormField label="Deck name" :error="editDeckError || undefined">
            <UInput v-model="editDeckName" class="w-full" autofocus @keyup.enter="submitEditDeck" />
          </UFormField>
          <UFormField label="Description" hint="optional">
            <UTextarea v-model="editDeckDesc" class="w-full" :rows="2" />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton color="neutral" variant="subtle" @click="isEditDeckOpen = false">
            Cancel
          </UButton>
          <UButton icon="i-lucide-check" @click="submitEditDeck">
            Save
          </UButton>
        </div>
      </template>
    </UModal>
  </UContainer>
</template>
