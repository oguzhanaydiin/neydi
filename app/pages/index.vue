<script setup lang="ts">
const { decks, createDeck, deleteDeck } = useDecks()

const isCreateOpen = ref(false)
const newDeckName = ref('')
const newDeckDesc = ref('')
const createError = ref('')

const openCreate = () => {
  newDeckName.value = ''
  newDeckDesc.value = ''
  createError.value = ''
  isCreateOpen.value = true
}

const submitCreate = () => {
  if (!newDeckName.value.trim()) {
    createError.value = 'Deck name is required'
    return
  }
  createDeck(newDeckName.value, newDeckDesc.value)
  isCreateOpen.value = false
}

const confirmDeleteId = ref<string | null>(null)

const confirmDelete = (id: string) => {
  confirmDeleteId.value = id
}

const doDelete = () => {
  if (confirmDeleteId.value) {
    deleteDeck(confirmDeleteId.value)
    confirmDeleteId.value = null
  }
}
</script>

<template>
  <UContainer class="py-12">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold">Your Decks</h1>
        <p class="text-muted mt-1">Pick a deck and start studying</p>
      </div>
      <UButton icon="i-lucide-plus" size="lg" @click="openCreate">
        New Deck
      </UButton>
    </div>

    <div v-if="decks.length === 0" class="py-24">
      <UEmpty
        icon="i-lucide-layers"
        title="No decks yet"
        description="Create your first deck to start learning"
      >
        <template #actions>
          <UButton icon="i-lucide-plus" @click="openCreate">
            Create a deck
          </UButton>
        </template>
      </UEmpty>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="deck in decks" :key="deck.id" class="relative group">
        <DeckCard :deck="deck" />
        <UButton
          icon="i-lucide-trash-2"
          color="error"
          variant="ghost"
          size="xs"
          class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
          @click="confirmDelete(deck.id)"
        />
      </div>
    </div>

    <!-- Create Deck Modal -->
    <UModal v-model:open="isCreateOpen" title="New Deck">
      <template #body>
        <div class="flex flex-col gap-4">
          <UFormField label="Deck name" :error="createError || undefined">
            <UInput
              v-model="newDeckName"
              placeholder="e.g. Spanish Vocabulary"
              class="w-full"
              autofocus
              @keyup.enter="submitCreate"
            />
          </UFormField>
          <UFormField label="Description" hint="optional">
            <UTextarea
              v-model="newDeckDesc"
              placeholder="What is this deck about?"
              class="w-full"
              :rows="2"
            />
          </UFormField>
        </div>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton color="neutral" variant="subtle" @click="isCreateOpen = false">
            Cancel
          </UButton>
          <UButton icon="i-lucide-plus" @click="submitCreate">
            Create Deck
          </UButton>
        </div>
      </template>
    </UModal>

    <!-- Delete Confirmation Modal -->
    <UModal
      :open="!!confirmDeleteId"
      title="Delete deck?"
      @update:open="confirmDeleteId = null"
    >
      <template #body>
        <p class="text-muted">
          This will permanently delete the deck and all its cards. This cannot be undone.
        </p>
      </template>
      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton color="neutral" variant="subtle" @click="confirmDeleteId = null">
            Cancel
          </UButton>
          <UButton color="error" icon="i-lucide-trash-2" @click="doDelete">
            Delete
          </UButton>
        </div>
      </template>
    </UModal>
  </UContainer>
</template>
