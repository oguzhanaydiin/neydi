<script setup lang="ts">
const props = defineProps<{
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  confirmColor?: string
  confirmIcon?: string
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: []
}>()

const confirmLabel = computed(() => props.confirmLabel ?? 'Delete')
const confirmColor = computed(() => props.confirmColor ?? 'error')
const confirmIcon = computed(() => props.confirmIcon ?? 'i-lucide-trash-2')

const close = () => emit('update:open', false)
</script>

<template>
  <UModal
    :open="open"
    :title="title"
    @update:open="emit('update:open', $event)"
  >
    <template #body>
      <p class="text-muted">{{ message }}</p>
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
          :color="confirmColor"
          :icon="confirmIcon"
          @click="emit('confirm')"
        >
          {{ confirmLabel }}
        </UButton>
      </div>
    </template>
  </UModal>
</template>
