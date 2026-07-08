<script setup lang="ts">
const { public: { apiBase } } = useRuntimeConfig()

const LIMIT = 10

interface UserPublicResponse {
  id: string
  username: string
  created_at: string
}

const route = useRoute()
const query = ref('')
const users = ref<UserPublicResponse[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const skip = ref(0)
const hasMore = ref(false)

const fetchUsers = async (reset = true) => {
  if (reset) {
    skip.value = 0
    users.value = []
    loading.value = true
  } else {
    loadingMore.value = true
  }

  try {
    const page = await $fetch<UserPublicResponse[]>(`${apiBase}/users/search`, {
      params: { q: query.value, skip: skip.value, limit: LIMIT }
    })
    users.value = reset ? page : [...users.value, ...page]
    hasMore.value = page.length === LIMIT
    skip.value += page.length
  } catch {
    if (reset) users.value = []
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null
watch(query, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => fetchUsers(true), 500)
})

onMounted(() => {
  const q = route.query.q
  if (typeof q === 'string' && q.trim()) {
    query.value = q.trim()
  }
  fetchUsers(true)
})

const formatDate = (dateStr: string) =>
  new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'long' })
</script>

<template>
  <UContainer class="py-12">
    <div class="mb-8">
      <h1 class="text-3xl font-bold">
        Users
      </h1>
      <p class="text-muted mt-1">
        Search for users and browse their decks
      </p>
    </div>

    <UInput
      v-model="query"
      placeholder="Search by username..."
      icon="i-lucide-search"
      size="lg"
      class="mb-6"
      :loading="loading"
    />

    <div
      v-if="loading"
      class="py-16 flex justify-center"
    >
      <UIcon
        name="i-lucide-loader-circle"
        class="animate-spin size-6 text-muted"
      />
    </div>

    <template v-else>
      <div
        v-if="users.length === 0"
        class="py-16"
      >
        <UEmpty
          icon="i-lucide-user-x"
          title="No users found"
          :description="query ? `No users matching '${query}'` : 'No users yet'"
        />
      </div>

      <div
        v-else
        class="flex flex-col gap-2"
      >
        <NuxtLink
          v-for="u in users"
          :key="u.id"
          :to="`/users/${u.id}`"
          class="block"
        >
          <UCard class="hover:shadow-md transition-shadow cursor-pointer">
            <div class="flex items-center gap-3">
              <div class="bg-primary/10 rounded-full size-10 flex items-center justify-center shrink-0">
                <UIcon
                  name="i-lucide-user"
                  class="size-5 text-primary"
                />
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-semibold">
                  {{ u.username }}
                </p>
                <p class="text-xs text-muted">
                  Joined {{ formatDate(u.created_at) }}
                </p>
              </div>
              <UIcon
                name="i-lucide-chevron-right"
                class="size-4 text-muted shrink-0"
              />
            </div>
          </UCard>
        </NuxtLink>

        <div
          v-if="hasMore"
          class="pt-4 flex justify-center"
        >
          <UButton
            variant="outline"
            :loading="loadingMore"
            icon="i-lucide-chevrons-down"
            @click="fetchUsers(false)"
          >
            Load more
          </UButton>
        </div>
      </div>
    </template>
  </UContainer>
</template>
