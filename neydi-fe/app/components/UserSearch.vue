<script setup lang="ts">
const { public: { apiBase } } = useRuntimeConfig()
const router = useRouter()

interface UserPublicResponse {
  id: string
  username: string
  created_at: string
}

const query = ref('')
const results = ref<UserPublicResponse[]>([])
const loading = ref(false)
const open = ref(false)
const root = ref<HTMLElement | null>(null)

const search = async () => {
  const q = query.value.trim()
  if (!q) {
    results.value = []
    open.value = false
    return
  }

  loading.value = true
  try {
    results.value = await $fetch<UserPublicResponse[]>(`${apiBase}/users/search`, {
      params: { q, limit: 8 }
    })
    open.value = true
  } catch {
    results.value = []
    open.value = false
  } finally {
    loading.value = false
  }
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null
watch(query, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(search, 500)
})

const goToUser = (user: UserPublicResponse) => {
  query.value = ''
  results.value = []
  open.value = false
  router.push(`/users/${user.id}`)
}

const goToBrowse = () => {
  const q = query.value.trim()
  query.value = ''
  results.value = []
  open.value = false
  router.push(q ? { path: '/users', query: { q } } : '/users')
}

const onSubmit = () => {
  if (results.value.length === 1) {
    goToUser(results.value[0])
  } else if (results.value.length > 1) {
    goToBrowse()
  } else if (query.value.trim()) {
    goToBrowse()
  }
}

const onFocus = () => {
  if (query.value.trim() && results.value.length) {
    open.value = true
  }
}

const onDocumentClick = (event: MouseEvent) => {
  if (!root.value?.contains(event.target as Node)) {
    open.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
})
</script>

<template>
  <div
    ref="root"
    class="relative w-full max-w-[160px] sm:max-w-xs"
  >
    <form @submit.prevent="onSubmit">
      <UInput
        v-model="query"
        placeholder="Search users or decks..."
        icon="i-lucide-search"
        size="sm"
        :loading="loading"
        @focus="onFocus"
      />
    </form>

    <div
      v-if="open && query.trim()"
      class="absolute top-full left-0 right-0 z-50 mt-1 rounded-lg border border-default bg-default shadow-lg overflow-hidden"
    >
      <div
        v-if="results.length === 0 && !loading"
        class="px-3 py-2.5 text-sm text-muted"
      >
        No users found
      </div>

      <button
        v-for="user in results"
        :key="user.id"
        type="button"
        class="flex w-full items-center gap-2.5 px-3 py-2 text-sm hover:bg-elevated transition-colors cursor-pointer"
        @click="goToUser(user)"
      >
        <div class="bg-primary/10 rounded-full size-7 flex items-center justify-center shrink-0">
          <UIcon
            name="i-lucide-user"
            class="size-3.5 text-primary"
          />
        </div>
        <span class="font-medium truncate">{{ user.username }}</span>
      </button>

      <button
        type="button"
        class="flex w-full items-center gap-2 px-3 py-2 text-xs text-muted border-t border-default hover:bg-elevated transition-colors cursor-pointer"
        @click="goToBrowse"
      >
        <UIcon
          name="i-lucide-users"
          class="size-3.5 shrink-0"
        />
        Browse all users
      </button>
    </div>
  </div>
</template>
