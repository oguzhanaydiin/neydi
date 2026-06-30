<script setup lang="ts">
const props = defineProps<{
  front: string
  back: string
  revealed: boolean
  confidence?: number
}>()

const emit = defineEmits<{
  toggle: []
}>()

const confidenceColor = computed(() => {
  const c = props.confidence ?? 0
  if (c === 0) return 'bg-muted'
  if (c <= 2) return 'bg-error'
  if (c <= 3) return 'bg-warning'
  if (c === 4) return 'bg-info'
  return 'bg-success'
})
</script>

<template>
  <div
    class="w-full max-w-xs sm:max-w-sm mx-auto aspect-5/7 perspective-card cursor-pointer select-none"
    @click="emit('toggle')"
  >
    <div
      class="w-full h-full relative transform-3d transition-transform duration-flip ease-in-out"
      :class="{ 'rotate-y-180': revealed }"
    >
      <!-- Front -->
      <div
        class="absolute inset-0 backface-hidden flex flex-col items-center justify-center gap-3 rounded-xl p-10 border border-default bg-default shadow-card"
      >
        <!-- Confidence dots -->
        <div class="absolute top-5 flex items-center gap-1.5">
          <div
            v-for="i in 5"
            :key="i"
            class="w-2 h-2 rounded-full transition-colors duration-200"
            :class="i <= (confidence ?? 0) ? confidenceColor : 'bg-muted/30'"
          />
        </div>

        <p
          class="text-[clamp(1.1rem,3vw,1.5rem)] font-medium text-center leading-[1.4] max-w-full wrap-break-word"
        >
          {{ front }}
        </p>

        <p
          class="text-xs text-muted absolute bottom-4 flex items-center gap-1"
        >
          <UIcon name="i-lucide-refresh-cw" class="size-3" />
          Tap to flip
        </p>
      </div>

      <!-- Back -->
      <div
        class="absolute inset-0 backface-hidden rotate-y-180 flex flex-col items-center justify-center gap-3 rounded-xl p-10 border border-default bg-elevated shadow-card"
      >
        <!-- Confidence dots (mirrored on back too) -->
        <div class="absolute top-5 flex items-center gap-1.5">
          <div
            v-for="i in 5"
            :key="i"
            class="w-2 h-2 rounded-full transition-colors duration-200"
            :class="i <= (confidence ?? 0) ? confidenceColor : 'bg-muted/30'"
          />
        </div>

        <p
          class="text-xs font-semibold tracking-[0.08em] uppercase text-primary absolute top-11"
        >
          Answer
        </p>
        <p
          class="text-[clamp(1.1rem,3vw,1.5rem)] font-medium text-center leading-[1.4] max-w-full wrap-break-word"
        >
          {{ back }}
        </p>

        <p
          class="text-xs text-muted absolute bottom-4 flex items-center gap-1"
        >
          <UIcon name="i-lucide-refresh-cw" class="size-3" />
          Tap to flip back
        </p>
      </div>
    </div>
  </div>
</template>
