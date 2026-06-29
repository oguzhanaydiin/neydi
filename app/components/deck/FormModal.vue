<script setup lang="ts">
import type { Deck } from '~/composables/useDecks'

const props = defineProps<{
  open: boolean
  deck?: Deck
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'submit': [name: string, desc: string]
}>()

const isEditMode = computed(() => !!props.deck)
const title = computed(() => isEditMode.value ? 'Edit Deck' : 'New Deck')
const submitLabel = computed(() => isEditMode.value ? 'Save' : 'Create Deck')
const submitIcon = computed(() => isEditMode.value ? 'i-lucide-check' : 'i-lucide-plus')

const name = ref('')
const desc = ref('')
const error = ref('')

watch(() => props.open, (val) => {
  if (val) {
    name.value = props.deck?.name ?? ''
    desc.value = props.deck?.description ?? ''
    error.value = ''
  }
})

const close = () => emit('update:open', false)

const submit = () => {
  if (!name.value.trim()) {
    error.value = 'Deck name is required'
    return
  }
  emit('submit', name.value, desc.value)
  close()
}
</script>

<template>
  <UModal
    :open="open"
    :title="title"
    @update:open="emit('update:open', $event)"
  >
    <template #body>
      <div
        class="flex flex-col gap-4"
      >
        <UFormField
          label="Deck name"
          :error="error || undefined"
        >
          <UInput
            v-model="name"
            placeholder="e.g. Spanish Vocabulary"
            class="w-full"
            autofocus
            @keyup.enter="submit"
          />
        </UFormField>
        <UFormField
          label="Description"
          hint="optional"
        >
          <UTextarea
            v-model="desc"
            placeholder="What is this deck about?"
            class="w-full"
            :rows="2"
          />
        </UFormField>
      </div>
    </template>
    <template #footer>
      <div
        class="flex justify-between gap-2 w-full"
      >
        <UButton
          color="neutral"
          variant="subtle"
          @click="close"
        >
          Cancel
        </UButton>
        <UButton
          :icon="submitIcon"
          @click="submit"
        >
          {{ submitLabel }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
