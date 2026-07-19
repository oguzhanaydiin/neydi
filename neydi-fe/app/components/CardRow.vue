<script setup lang="ts">
import type { Card } from '~/composables/useDecks'

const props = defineProps<{
  card: Card
  index: number
  draggable?: boolean
  readonly?: boolean
  gripListeners?: { onPointerdown: (e: PointerEvent) => void }
}>()

defineEmits<{
  edit: []
  delete: []
}>()

const confidenceDotClass = (i: number) => {
  if (i > (props.card.confidence ?? 0)) return 'bg-muted/30'
  const c = props.card.confidence ?? 0
  if (c <= 2) return 'bg-error'
  if (c === 3) return 'bg-warning'
  if (c === 4) return 'bg-info'
  return 'bg-success'
}

const confidenceLabel = computed(() => {
  const c = props.card.confidence ?? 0
  const labels = ['New', 'Seen', 'Learning', 'Familiar', 'Strong', 'Mastered']
  return `${labels[c]} (${c}/5)`
})
</script>

<template>
  <div class="flex items-center gap-3">
    <!-- Number + optional drag handle -->
    <div class="flex items-center gap-1.5 shrink-0">
      <span class="text-sm font-mono text-muted w-6 text-right leading-none">{{ index + 1 }}</span>
      <div
        v-if="draggable"
        class="cursor-grab active:cursor-grabbing text-muted hover:text-default transition-colors flex items-center touch-none"
        v-bind="gripListeners"
      >
        <UIcon
          name="i-lucide-grip-vertical"
          class="size-4"
        />
      </div>
      <div
        v-else
        class="w-4"
      />
    </div>

    <div class="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4 min-w-0">
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

    <div class="flex items-center gap-3 shrink-0 self-center">
      <!-- Confidence dots with tooltip -->
      <UTooltip
        :text="confidenceLabel"
        class="hidden sm:flex"
      >
        <div class="flex items-center gap-1 cursor-default">
          <div
            v-for="i in 5"
            :key="i"
            class="w-1.5 h-1.5 rounded-full"
            :class="confidenceDotClass(i)"
          />
        </div>
      </UTooltip>

      <div
        v-if="!readonly"
        class="flex gap-1"
      >
        <UButton
          icon="i-lucide-pencil"
          size="xs"
          color="neutral"
          variant="ghost"
          @click="$emit('edit')"
        />
        <UButton
          icon="i-lucide-trash-2"
          size="xs"
          color="error"
          variant="ghost"
          @click="$emit('delete')"
        />
      </div>
    </div>
  </div>
</template>
