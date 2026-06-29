<script setup lang="ts">
const { decks, createDeck, deleteDeck } = useDecks()

const isDeckFormOpen = ref(false)
const deletingDeckId = ref<string | null>(null)
const isDeleteOpen = ref(false)

const openDelete = (id: string) => {
  deletingDeckId.value = id
  isDeleteOpen.value = true
}

watch(isDeleteOpen, (val) => { if (!val) deletingDeckId.value = null })

const handleCreate = (name: string, desc: string) => {
  createDeck(name, desc)
}

const handleDelete = () => {
  if (deletingDeckId.value) {
    deleteDeck(deletingDeckId.value)
    isDeleteOpen.value = false
  }
}
</script>

<template>
  <UContainer
    class="py-12"
  >
    <div
      class="flex flex-wrap items-center justify-between gap-4 mb-8"
    >
      <div>
        <h1 class="text-3xl font-bold">Your Decks</h1>
        <p class="text-muted mt-1">Pick a deck and start studying</p>
      </div>
      <UButton
        icon="i-lucide-plus"
        size="lg"
        @click="isDeckFormOpen = true"
      >
        New Deck
      </UButton>
    </div>

    <div
      v-show="decks.length === 0"
      class="py-24"
    >
      <UEmpty
        icon="i-lucide-layers"
        title="No decks yet"
        description="Create your first deck to start learning"
      >
        <template #actions>
          <UButton
            icon="i-lucide-plus"
            @click="isDeckFormOpen = true"
          >
            Create a deck
          </UButton>
        </template>
      </UEmpty>
    </div>

    <div
      v-show="decks.length > 0"
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
    >
      <div
        v-for="deck in decks"
        :key="deck.id"
        class="relative group"
      >
        <DeckCard :deck="deck" />
        <UButton
          icon="i-lucide-trash-2"
          color="error"
          variant="ghost"
          size="xs"
          class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
          @click="openDelete(deck.id)"
        />
      </div>
    </div>

    <DeckFormModal
      v-model:open="isDeckFormOpen"
      @submit="handleCreate"
    />

    <AppConfirmModal
      v-model:open="isDeleteOpen"
      title="Delete deck?"
      message="This will permanently delete the deck and all its cards. This cannot be undone."
      @confirm="handleDelete"
    />
  </UContainer>
</template>
