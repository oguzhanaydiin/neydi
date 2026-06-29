<script setup lang="ts">
import type { Theme } from '~/composables/useTheme'

const { theme, setTheme } = useTheme()

const themes: { id: Theme, label: string, swatches: [string, string, string] }[] = [
  {
    id: 'dark',
    label: 'Dark',
    swatches: ['#0f172a', '#22c55e', '#64748b']
  },
  {
    id: 'light',
    label: 'Light',
    swatches: ['#f8fafc', '#22c55e', '#94a3b8']
  },
  {
    id: 'lahmacun',
    label: 'Lahmacun',
    swatches: ['#e4d0a0', '#c02e10', '#35180a']
  },
  {
    id: 'strawberry-shortcake',
    label: 'Strawberry Shortcake',
    swatches: ['#fdeef3', '#f03660', '#f2cad8']
  },
  {
    id: 'vulnicura',
    label: 'Vulnicura',
    swatches: ['#09080a', '#c0a020', '#d4b84a']
  }
]
</script>

<template>
  <UPopover :ui="{ content: 'p-0 w-52' }">
    <button
      type="button"
      class="px-3 py-1.5 rounded-lg text-sm font-medium border border-default text-muted hover:text-default hover:bg-elevated transition-all duration-200 cursor-pointer"
      aria-label="Switch theme"
    >
      Theme
    </button>

    <template #content>
      <div class="flex flex-col py-1">
        <button
          v-for="t in themes"
          :key="t.id"
          type="button"
          class="flex items-center gap-2.5 px-3 py-2 text-sm transition-colors cursor-pointer"
          :class="theme === t.id
            ? 'text-primary bg-primary/10 font-medium'
            : 'text-default hover:bg-elevated'"
          @click="setTheme(t.id)"
        >
          <div class="flex gap-0.5 shrink-0">
            <span
              v-for="(color, i) in t.swatches"
              :key="i"
              class="block w-3 h-3 rounded-sm"
              :style="{ backgroundColor: color }"
            />
          </div>
          <span class="grow text-left">{{ t.label }}</span>
          <UIcon
            v-if="theme === t.id"
            name="i-lucide-check"
            class="shrink-0 w-3.5 h-3.5"
          />
        </button>
      </div>
    </template>
  </UPopover>
</template>
