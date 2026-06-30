<script setup lang="ts">
const props = defineProps<{
  front: string
  back: string
  revealed: boolean
  confidence?: number
}>()

const emit = defineEmits<{
  toggle: []
  known: []
  unknown: []
}>()

// --- Drag state ---
const dragX = ref(0)
const isDragging = ref(false)
const startX = ref(0)
const hasDragged = ref(false)
const isLeaving = ref(false)
const leaveDirection = ref<'left' | 'right' | null>(null)
const leaveFromX = ref(0)
const leaveFromY = ref(0)

const SWIPE_THRESHOLD = 80

// --- Drag styles ---
const wrapperStyle = computed(() => {
  if (isLeaving.value) {
    // Pass captured release position as CSS vars for the keyframe `from` state
    return {
      '--leave-x': `${leaveFromX.value}px`,
      '--leave-y': `${leaveFromY.value}px`
    }
  }
  if (!isDragging.value && dragX.value === 0) return {}
  const dragY = Math.abs(dragX.value) * 0.15
  return {
    transform: `translateX(${dragX.value}px) translateY(${dragY}px)`,
    transition: isDragging.value ? 'none' : 'transform 0.35s cubic-bezier(0.25,0.46,0.45,0.94)'
  }
})

const wrapperClass = computed(() => {
  if (!isLeaving.value) return ''
  return leaveDirection.value === 'right' ? 'swipe-out-right' : 'swipe-out-left'
})

// --- Overlays ---
const overlayOpacity = computed(() => Math.min(Math.abs(dragX.value) / 100, 0.75))
const showKnowOverlay = computed(() => dragX.value > 20)
const showNopeOverlay = computed(() => dragX.value < -20)

// --- Confidence dot color ---
const confidenceColor = computed(() => {
  const c = props.confidence ?? 0
  if (c === 0) return 'bg-muted'
  if (c <= 2) return 'bg-error'
  if (c === 3) return 'bg-warning'
  if (c === 4) return 'bg-info'
  return 'bg-success'
})

// --- Pointer events ---
const onPointerDown = (e: PointerEvent) => {
  isDragging.value = true
  hasDragged.value = false
  startX.value = e.clientX
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}

const onPointerMove = (e: PointerEvent) => {
  if (!isDragging.value) return
  const dx = e.clientX - startX.value
  dragX.value = dx
  if (Math.abs(dx) > 6) hasDragged.value = true
}

const onPointerUp = () => {
  if (!isDragging.value) return
  isDragging.value = false

  if (!hasDragged.value) {
    dragX.value = 0
    emit('toggle')
    return
  }

  if (dragX.value > SWIPE_THRESHOLD) {
    swipeOut('right')
  } else if (dragX.value < -SWIPE_THRESHOLD) {
    swipeOut('left')
  } else {
    dragX.value = 0
  }
}

// --- Swipe out (called externally via ref OR from gesture) ---
const swipeOut = (direction: 'left' | 'right') => {
  // Capture where the card is right now so the animation starts from there
  leaveFromX.value = dragX.value
  leaveFromY.value = Math.abs(dragX.value) * 0.15
  dragX.value = 0
  isLeaving.value = true
  leaveDirection.value = direction
  setTimeout(() => {
    if (direction === 'right') emit('known')
    else emit('unknown')
  }, 320)
}

defineExpose({ swipeOut })
</script>

<template>
  <div
    class="relative w-full max-w-xs sm:max-w-sm mx-auto select-none touch-none"
    :class="wrapperClass"
    :style="wrapperStyle"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
  >
    <!-- KNOW stamp -->
    <div
      v-if="showKnowOverlay || (isLeaving && leaveDirection === 'right')"
      class="absolute inset-0 z-10 rounded-xl flex items-center justify-center pointer-events-none overflow-hidden"
      :style="{ backgroundColor: `rgba(34,197,94,${isLeaving ? 0.5 : overlayOpacity})` }"
    >
      <span
        class="text-white font-black text-3xl tracking-widest border-4 border-white/90 rounded-lg px-5 py-1.5 rotate-[-20deg] drop-shadow"
      >
        KNOW
      </span>
    </div>

    <!-- NOPE stamp -->
    <div
      v-if="showNopeOverlay || (isLeaving && leaveDirection === 'left')"
      class="absolute inset-0 z-10 rounded-xl flex items-center justify-center pointer-events-none overflow-hidden"
      :style="{ backgroundColor: `rgba(239,68,68,${isLeaving ? 0.5 : overlayOpacity})` }"
    >
      <span
        class="text-white font-black text-3xl tracking-widest border-4 border-white/90 rounded-lg px-5 py-1.5 rotate-20 drop-shadow"
      >
        NOPE
      </span>
    </div>

    <!-- Card -->
    <div class="aspect-5/7 perspective-card cursor-grab active:cursor-grabbing">
      <div
        class="w-full h-full relative transform-3d transition-transform duration-flip ease-in-out"
        :class="{ 'rotate-y-180': revealed }"
      >
        <!-- Front -->
        <div
          class="absolute inset-0 backface-hidden flex flex-col items-center justify-center gap-3 rounded-xl p-10 border border-default bg-default shadow-card"
        >
          <div class="absolute top-5 flex items-center gap-1.5">
            <div
              v-for="i in 5"
              :key="i"
              class="w-2 h-2 rounded-full transition-colors duration-200"
              :class="i <= (confidence ?? 0) ? confidenceColor : 'bg-muted/30'"
            />
          </div>

          <p class="text-[clamp(1.1rem,3vw,1.5rem)] font-medium text-center leading-[1.4] max-w-full wrap-break-word">
            {{ front }}
          </p>

          <p class="text-xs text-muted absolute bottom-4 flex items-center gap-1.5">
            <UIcon
              name="i-lucide-refresh-cw"
              class="size-3"
            />
            Tap to flip · swipe to answer
          </p>
        </div>

        <!-- Back -->
        <div
          class="absolute inset-0 backface-hidden rotate-y-180 flex flex-col items-center justify-center gap-3 rounded-xl p-10 border border-default bg-elevated shadow-card"
        >
          <div class="absolute top-5 flex items-center gap-1.5">
            <div
              v-for="i in 5"
              :key="i"
              class="w-2 h-2 rounded-full transition-colors duration-200"
              :class="i <= (confidence ?? 0) ? confidenceColor : 'bg-muted/30'"
            />
          </div>

          <p class="text-xs font-semibold tracking-[0.08em] uppercase text-primary absolute top-11">
            Answer
          </p>

          <p class="text-[clamp(1.1rem,3vw,1.5rem)] font-medium text-center leading-[1.4] max-w-full wrap-break-word">
            {{ back }}
          </p>

          <p class="text-xs text-muted absolute bottom-4 flex items-center gap-1.5">
            <UIcon
              name="i-lucide-refresh-cw"
              class="size-3"
            />
            Tap to flip back
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.swipe-out-right {
  animation: swipe-right 0.32s ease-in forwards;
}
.swipe-out-left {
  animation: swipe-left 0.32s ease-in forwards;
}

@keyframes swipe-right {
  from {
    transform: translateX(var(--leave-x, 0px)) translateY(var(--leave-y, 0px));
    opacity: 1;
  }
  to {
    transform: translateX(140%) translateY(20%);
    opacity: 0;
  }
}
@keyframes swipe-left {
  from {
    transform: translateX(var(--leave-x, 0px)) translateY(var(--leave-y, 0px));
    opacity: 1;
  }
  to {
    transform: translateX(-140%) translateY(20%);
    opacity: 0;
  }
}
</style>
