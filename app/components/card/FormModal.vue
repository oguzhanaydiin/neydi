<script setup lang="ts">
import type { Card } from '~/composables/useDecks'

const props = defineProps<{
  open: boolean
  card?: Card | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'submit': [front: string, back: string]
}>()

const isEditMode = computed(() => !!props.card)
const title = computed(() => isEditMode.value ? 'Edit Card' : 'Add Card')
const submitLabel = computed(() => isEditMode.value ? 'Save' : 'Add Card')
const submitIcon = computed(() => isEditMode.value ? 'i-lucide-check' : 'i-lucide-plus')

const front = ref('')
const back = ref('')
const errors = ref({ front: '', back: '' })

watch(() => props.open, (val) => {
  if (val) {
    front.value = props.card?.front ?? ''
    back.value = props.card?.back ?? ''
    errors.value = { front: '', back: '' }
  }
})

const close = () => emit('update:open', false)

const submit = () => {
  errors.value = { front: '', back: '' }
  let valid = true
  if (!front.value.trim()) {
    errors.value.front = 'Required'
    valid = false
  }
  if (!back.value.trim()) {
    errors.value.back = 'Required'
    valid = false
  }
  if (!valid) return
  emit('submit', front.value, back.value)
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
          label="Front"
          :error="errors.front || undefined"
        >
          <UTextarea
            v-model="front"
            placeholder="Question or term"
            class="w-full"
            :rows="3"
            autofocus
          />
        </UFormField>
        <UFormField
          label="Back"
          :error="errors.back || undefined"
        >
          <UTextarea
            v-model="back"
            placeholder="Answer or definition"
            class="w-full"
            :rows="3"
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
