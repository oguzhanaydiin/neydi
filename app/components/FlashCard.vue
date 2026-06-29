<script setup lang="ts">
const props = defineProps<{
  front: string
  back: string
  revealed: boolean
}>()

const emit = defineEmits<{
  reveal: []
}>()

const onClick = () => {
  if (!props.revealed) emit('reveal')
}
</script>

<template>
  <div
    class="w-full max-w-xs sm:max-w-sm mx-auto aspect-5/7 perspective-card cursor-pointer select-none"
    @click="onClick"
  >
    <div
      class="w-full h-full relative transform-3d transition-transform duration-flip ease-in-out"
      :class="{ 'rotate-y-180': revealed }"
    >
      <!-- Front -->
      <div
        class="absolute inset-0 backface-hidden flex flex-col items-center justify-center gap-3 rounded-xl p-10 border border-default bg-default shadow-card"
      >
        <p
          class="text-[clamp(1.1rem,3vw,1.5rem)] font-medium text-center leading-[1.4] max-w-full wrap-break-word"
        >
          {{ front }}
        </p>
        <p
          class="text-xs text-muted absolute bottom-5 flex items-center gap-1"
        >
          <UIcon name="i-lucide-mouse-pointer-click" />
          Click to reveal
        </p>
      </div>

      <!-- Back -->
      <div
        class="absolute inset-0 backface-hidden rotate-y-180 flex flex-col items-center justify-center gap-3 rounded-xl p-10 border border-default bg-elevated shadow-card"
      >
        <p
          class="text-xs font-semibold tracking-[0.08em] uppercase text-primary absolute top-5"
        >
          Answer
        </p>
        <p
          class="text-[clamp(1.1rem,3vw,1.5rem)] font-medium text-center leading-[1.4] max-w-full wrap-break-word"
        >
          {{ back }}
        </p>
      </div>
    </div>
  </div>
</template>
