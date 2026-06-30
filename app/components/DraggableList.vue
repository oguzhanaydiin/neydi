<script setup lang="ts" generic="T">
const props = defineProps<{
  items: T[]
  gap?: number // px, matches the CSS gap between items (default 12 = gap-3)
}>()

const emit = defineEmits<{
  reorder: [items: T[]]
}>()

const dragSrc = ref<number | null>(null)
const dragTgt = ref<number | null>(null)
const dragOffsetY = ref(0)
const dragStartY = ref(0)
const dragItemHeight = ref(0)
const originalRects = ref<DOMRect[]>([])
const itemEls = ref<(HTMLElement | null)[]>([])

const isDragging = computed(() => dragSrc.value !== null)

const setItemEl = (i: number, el: unknown) => {
  itemEls.value[i] = el as HTMLElement | null
}

const onGripDown = (e: PointerEvent, index: number) => {
  // Snapshot rects before any transforms are applied
  originalRects.value = itemEls.value.map(el => el?.getBoundingClientRect() ?? new DOMRect())
  dragItemHeight.value = originalRects.value[index]?.height ?? 0
  dragSrc.value = index
  dragTgt.value = index
  dragStartY.value = e.clientY
  dragOffsetY.value = 0
  document.addEventListener('pointermove', onPointerMove)
  document.addEventListener('pointerup', onPointerUp, { once: true })
}

const onPointerMove = (e: PointerEvent) => {
  if (dragSrc.value === null) return
  dragOffsetY.value = e.clientY - dragStartY.value

  const src = dragSrc.value
  const n = originalRects.value.length
  let newTgt = src

  for (let i = src + 1; i < n; i++) {
    const r = originalRects.value[i]!
    if (e.clientY > r.top + r.height / 2) newTgt = i
    else break
  }
  if (newTgt === src) {
    for (let i = src - 1; i >= 0; i--) {
      const r = originalRects.value[i]!
      if (e.clientY < r.top + r.height / 2) newTgt = i
      else break
    }
  }

  dragTgt.value = newTgt
}

const onPointerUp = () => {
  document.removeEventListener('pointermove', onPointerMove)
  const src = dragSrc.value
  const tgt = dragTgt.value
  if (src !== null && tgt !== null && src !== tgt) {
    const arr = [...props.items]
    const [moved] = arr.splice(src, 1)
    arr.splice(tgt, 0, moved!)
    emit('reorder', arr)
  }
  dragSrc.value = null
  dragTgt.value = null
  dragOffsetY.value = 0
}

onUnmounted(() => {
  document.removeEventListener('pointermove', onPointerMove)
  document.removeEventListener('pointerup', onPointerUp)
})

const itemStyle = (index: number): Record<string, string> => {
  const src = dragSrc.value
  const tgt = dragTgt.value
  if (src === null || tgt === null) return {}

  const shift = `${dragItemHeight.value + (props.gap ?? 12)}px`

  if (index === src) {
    return {
      transform: `translateY(${dragOffsetY.value}px)`,
      zIndex: '20',
      position: 'relative',
      transition: 'box-shadow 150ms ease'
    }
  }
  if (src < tgt && index > src && index <= tgt) {
    return { transform: `translateY(-${shift})`, transition: 'transform 150ms ease' }
  }
  if (src > tgt && index < src && index >= tgt) {
    return { transform: `translateY(${shift})`, transition: 'transform 150ms ease' }
  }
  return { transition: 'transform 150ms ease' }
}
</script>

<template>
  <div :class="{ 'select-none': isDragging }">
    <div
      v-for="(item, i) in items"
      :key="i"
      :ref="(el: unknown) => setItemEl(i, el)"
      :style="itemStyle(i)"
      class="transition-shadow duration-150"
      :class="{ 'shadow-xl rounded-xl': dragSrc === i }"
    >
      <slot
        :item="item"
        :index="i"
        :grip-listeners="{ onPointerdown: (e: PointerEvent) => onGripDown(e, i) }"
      />
    </div>
  </div>
</template>
