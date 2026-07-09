<script setup lang="ts">
import {
  useFollow,
  type UserProfileResponse,
  type UserPublicResponse
} from '~/composables/useFollow'

const route = useRoute()
const { public: { apiBase } } = useRuntimeConfig()
const { user: currentUser, isLoggedIn } = useAuth()
const { getProfile, getFollowStatus, toggleFollow, getFollowers } = useFollow()

interface Card {
  id: string
  front: string
  back: string
  confidence: number
}

interface Deck {
  id: string
  name: string
  description?: string
  cards: Card[]
  createdAt: number
}

const userId = route.params.id as string
const user = ref<UserProfileResponse | null>(null)
const decks = ref<Deck[]>([])
const followers = ref<UserPublicResponse[]>([])
const isFollowing = ref(false)
const loading = ref(true)
const followLoading = ref(false)
const followersLoading = ref(false)
const view = ref<'decks' | 'followers'>('decks')
const expandedDecks = ref<Set<string>>(new Set())

const isOwnProfile = computed(() => currentUser.value?.id === userId)

const toggleDeck = (deckId: string) => {
  const next = new Set(expandedDecks.value)
  if (next.has(deckId)) {
    next.delete(deckId)
  } else {
    next.add(deckId)
  }
  expandedDecks.value = next
}

const showFollowers = async () => {
  view.value = 'followers'
  followersLoading.value = true
  try {
    followers.value = await getFollowers(userId)
  } finally {
    followersLoading.value = false
  }
}

const showDecks = () => {
  view.value = 'decks'
}

const loadFollowStatus = async () => {
  if (!isLoggedIn.value || isOwnProfile.value) return
  try {
    const status = await getFollowStatus(userId)
    isFollowing.value = status.is_following
  } catch {
    // auth expired or unavailable — profile still works without follow state
  }
}

onMounted(async () => {
  try {
    const [userRes, decksRes] = await Promise.all([
      getProfile(userId),
      $fetch<Deck[]>(`${apiBase}/users/${userId}/decks`)
    ])
    user.value = userRes
    decks.value = decksRes
  } catch {
    navigateTo('/users')
    return
  } finally {
    loading.value = false
  }

  await loadFollowStatus()
})

watch(isLoggedIn, (loggedIn) => {
  if (loggedIn) loadFollowStatus()
})

const handleToggleFollow = async () => {
  if (!user.value || !isLoggedIn.value) {
    navigateTo('/login')
    return
  }

  followLoading.value = true
  try {
    const status = await toggleFollow(userId)
    isFollowing.value = status.is_following
    user.value = {
      ...user.value,
      followers_count: user.value.followers_count + (status.is_following ? 1 : -1)
    }
    if (view.value === 'followers') {
      if (status.is_following && currentUser.value) {
        followers.value = [
          {
            id: currentUser.value.id,
            username: currentUser.value.username,
            created_at: currentUser.value.created_at
          },
          ...followers.value.filter(u => u.id !== currentUser.value?.id)
        ]
      } else {
        followers.value = followers.value.filter(u => u.id !== currentUser.value?.id)
      }
    }
  } finally {
    followLoading.value = false
  }
}

const totalCards = computed(() => decks.value.reduce((acc, d) => acc + d.cards.length, 0))

const formatDate = (dateStr: string) =>
  new Date(dateStr).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })

const confidenceDotClass = (card: Card, i: number) => {
  if (i > (card.confidence ?? 0)) return 'bg-muted/30'
  const c = card.confidence ?? 0
  if (c <= 2) return 'bg-error'
  if (c === 3) return 'bg-warning'
  if (c === 4) return 'bg-info'
  return 'bg-success'
}
</script>

<template>
  <UContainer class="py-10">
    <div
      v-if="loading"
      class="py-24 flex justify-center"
    >
      <UIcon
        name="i-lucide-loader-circle"
        class="animate-spin size-8 text-muted"
      />
    </div>

    <template v-else-if="user">
      <UBreadcrumb
        :items="[{ label: 'Users', to: '/users' }, { label: user.username }]"
        class="mb-6"
      />

      <!-- User Header -->
      <div class="flex flex-wrap items-center gap-4 mb-8">
        <div class="bg-primary/10 rounded-full p-4 shrink-0">
          <UIcon
            name="i-lucide-user"
            class="size-8 text-primary"
          />
        </div>
        <div class="flex-1 min-w-0">
          <h1 class="text-3xl font-bold">
            {{ user.username }}
          </h1>
          <p class="text-muted mt-0.5 text-sm">
            Joined {{ formatDate(user.created_at) }}
          </p>
        </div>

        <UButton
          v-if="!isOwnProfile"
          :variant="isFollowing ? 'outline' : 'solid'"
          :color="isFollowing ? 'neutral' : 'primary'"
          :loading="followLoading"
          :icon="isFollowing ? 'i-lucide-user-minus' : 'i-lucide-user-plus'"
          @click="handleToggleFollow"
        >
          {{ isFollowing ? 'Unfollow' : (isLoggedIn ? 'Follow' : 'Log in to follow') }}
        </UButton>

        <div class="flex gap-3 w-full sm:w-auto">
          <button
            class="text-center cursor-pointer hover:opacity-80 transition-opacity"
            @click="showFollowers"
          >
            <p class="text-2xl font-bold text-primary">
              {{ user.followers_count }}
            </p>
            <p class="text-xs text-muted">
              {{ user.followers_count === 1 ? 'Follower' : 'Followers' }}
            </p>
          </button>
          <div class="text-center">
            <p class="text-2xl font-bold text-primary">
              {{ user.following_count }}
            </p>
            <p class="text-xs text-muted">
              Following
            </p>
          </div>
          <div class="text-center">
            <p class="text-2xl font-bold text-primary">
              {{ decks.length }}
            </p>
            <p class="text-xs text-muted">
              {{ decks.length === 1 ? 'Deck' : 'Decks' }}
            </p>
          </div>
          <div class="text-center">
            <p class="text-2xl font-bold text-primary">
              {{ totalCards }}
            </p>
            <p class="text-xs text-muted">
              Cards
            </p>
          </div>
        </div>
      </div>

      <!-- Followers view -->
      <div v-if="view === 'followers'">
        <div class="flex items-center gap-2 mb-6">
          <UButton
            variant="ghost"
            color="neutral"
            icon="i-lucide-arrow-left"
            @click="showDecks"
          >
            Back to decks
          </UButton>
        </div>

        <div
          v-if="followersLoading"
          class="py-16 flex justify-center"
        >
          <UIcon
            name="i-lucide-loader-circle"
            class="animate-spin size-6 text-muted"
          />
        </div>

        <div
          v-else-if="followers.length === 0"
          class="py-16"
        >
          <UEmpty
            icon="i-lucide-users"
            title="No followers yet"
            :description="`${user.username} doesn't have any followers yet`"
          />
        </div>

        <div
          v-else
          class="flex flex-col gap-2"
        >
          <NuxtLink
            v-for="u in followers"
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
        </div>
      </div>

      <!-- Decks (default) -->
      <div v-else>
        <div
          v-if="decks.length === 0"
          class="py-20"
        >
          <UEmpty
            icon="i-lucide-layers"
            title="No decks yet"
            :description="`${user.username} hasn't created any decks yet`"
          />
        </div>

        <div
          v-else
          class="flex flex-col gap-4"
        >
          <p class="text-sm text-muted mb-2">
            {{ decks.length }} {{ decks.length === 1 ? 'deck' : 'decks' }} · {{ totalCards }} {{ totalCards === 1 ? 'card' : 'cards' }}
          </p>

          <div
            v-for="deck in decks"
            :key="deck.id"
          >
            <UCard>
              <div
                class="flex items-center gap-3 cursor-pointer select-none"
                @click="toggleDeck(deck.id)"
              >
                <div class="flex-1 min-w-0">
                  <h3 class="font-semibold text-lg leading-tight">
                    {{ deck.name }}
                  </h3>
                  <p
                    v-if="deck.description"
                    class="text-sm text-muted mt-0.5 line-clamp-1"
                  >
                    {{ deck.description }}
                  </p>
                </div>

                <div class="flex items-center gap-3 shrink-0">
                  <UBadge
                    :label="`${deck.cards.length} ${deck.cards.length === 1 ? 'card' : 'cards'}`"
                    variant="subtle"
                    color="neutral"
                    size="sm"
                  />
                  <UIcon
                    :name="expandedDecks.has(deck.id) ? 'i-lucide-chevron-up' : 'i-lucide-chevron-down'"
                    class="size-4 text-muted transition-transform"
                  />
                </div>
              </div>

              <div
                v-if="expandedDecks.has(deck.id)"
                class="mt-4 border-t pt-4 flex flex-col gap-3"
              >
                <div
                  v-if="deck.cards.length === 0"
                  class="py-6 text-center text-muted text-sm"
                >
                  No cards in this deck yet
                </div>

                <div
                  v-for="(card, index) in deck.cards"
                  :key="card.id"
                  class="flex items-start gap-3"
                >
                  <span class="text-sm font-mono text-muted w-6 text-right shrink-0 pt-0.5">
                    {{ index + 1 }}
                  </span>
                  <div class="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-3 min-w-0">
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
                  <div class="hidden sm:flex items-center gap-1 shrink-0 pt-1">
                    <div
                      v-for="i in 5"
                      :key="i"
                      class="w-1.5 h-1.5 rounded-full"
                      :class="confidenceDotClass(card, i)"
                    />
                  </div>
                </div>
              </div>
            </UCard>
          </div>
        </div>
      </div>
    </template>
  </UContainer>
</template>
