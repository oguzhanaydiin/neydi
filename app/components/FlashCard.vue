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
  <div class="card-scene" @click="onClick">
    <div class="card" :class="{ 'is-flipped': revealed }">
      <div class="card-face card-front">
        <p class="card-text">{{ front }}</p>
        <p class="card-hint">
          <UIcon name="i-lucide-mouse-pointer-click" class="inline mr-1" />
          Click to reveal
        </p>
      </div>
      <div class="card-face card-back">
        <p class="card-label">Answer</p>
        <p class="card-text">{{ back }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card-scene {
  width: 100%;
  height: 300px;
  perspective: 1200px;
  cursor: pointer;
  user-select: none;
}

.card {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.55s cubic-bezier(0.4, 0, 0.2, 1);
}

.card.is-flipped {
  transform: rotateY(180deg);
}

.card-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  border-radius: var(--ui-radius-lg, 0.75rem);
  padding: 2.5rem;
  border: 1px solid var(--ui-border);
  background: var(--ui-bg);
  box-shadow: 0 4px 24px -4px rgb(0 0 0 / 0.08);
}

.card-back {
  transform: rotateY(180deg);
  background: var(--ui-bg-elevated);
}

.card-text {
  font-size: clamp(1.1rem, 3vw, 1.5rem);
  font-weight: 500;
  text-align: center;
  line-height: 1.4;
  max-width: 100%;
  word-break: break-word;
}

.card-hint {
  font-size: 0.8rem;
  color: var(--ui-text-muted);
  position: absolute;
  bottom: 1.25rem;
}

.card-label {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ui-color-primary-500);
  position: absolute;
  top: 1.25rem;
}
</style>
