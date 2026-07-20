const STORAGE_KEY = 'neydi-decks'

export interface Card {
  id: string
  front: string
  back: string
  confidence: number // 0 = new, 5 = mastered
}

export interface Deck {
  id: string
  name: string
  description?: string
  cards: Card[]
  createdAt: number
  ownerUsername?: string
  ownerId?: string
  isPinned?: boolean
  saveCount?: number
}

export const useDecks = () => {
  const { public: { apiBase } } = useRuntimeConfig()
  const { isLoggedIn, token } = useAuth()

  const decks = useState<Deck[]>('decks', () => [])
  const pinnedDecks = useState<Deck[]>('pinnedDecks', () => [])
  const decksReady = useState('decksReady', () => false)

  const authHeaders = computed(() => ({
    Authorization: `Bearer ${token.value}`
  }))

  // --- Local persistence (guest only) ---

  const persist = () => {
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(decks.value))
    }
  }

  // --- Server sync (authenticated) ---

  const markDecksReady = () => {
    decksReady.value = true
  }

  // Fetch all decks from server. Called after restoreSession() in app.vue.
  const loadDecks = async () => {
    try {
      const [owned, pinned] = await Promise.all([
        $fetch<Deck[]>(`${apiBase}/decks`, { headers: authHeaders.value }),
        $fetch<Array<Deck & { owner_id: string, owner_username: string, save_count: number }>>(
          `${apiBase}/decks/pinned`,
          { headers: authHeaders.value }
        )
      ])
      decks.value = owned.map(d => ({ ...d, isPinned: false }))
      pinnedDecks.value = pinned.map(d => ({
        id: d.id,
        name: d.name,
        description: d.description,
        cards: d.cards,
        createdAt: d.createdAt,
        ownerId: d.owner_id,
        ownerUsername: d.owner_username,
        saveCount: d.save_count,
        isPinned: true
      }))
    } finally {
      decksReady.value = true
    }
  }

  // Migrate guest decks to server right after login. Local always wins on conflict.
  const migrateLocalDecks = async () => {
    if (!import.meta.client) return
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return
    let localDecks: Deck[]
    try { localDecks = JSON.parse(stored) as Deck[] } catch { return }
    if (localDecks.length === 0) return

    // PUT overwrites if the deck already exists in DB, 404 means create it fresh.
    await Promise.allSettled(localDecks.map(async (deck) => {
      try {
        await $fetch(`${apiBase}/decks/${deck.id}`, {
          method: 'PUT',
          headers: authHeaders.value,
          body: deck
        })
      } catch (err) {
        const status = (err as { status?: number, statusCode?: number })?.status
          ?? (err as { status?: number, statusCode?: number })?.statusCode
        if (status === 404) {
          await $fetch(`${apiBase}/decks`, {
            method: 'POST',
            headers: authHeaders.value,
            body: deck
          })
        }
      }
    }))

    localStorage.removeItem(STORAGE_KEY)
  }

  // --- Deck CRUD ---

  const getDeck = (id: string): Deck | undefined =>
    decks.value.find(d => d.id === id) ?? pinnedDecks.value.find(d => d.id === id)

  const isOwnedDeck = (id: string): boolean =>
    decks.value.some(d => d.id === id)

  const isDeckPinned = (id: string): boolean =>
    pinnedDecks.value.some(d => d.id === id)

  const createDeck = async (name: string, description?: string): Promise<Deck> => {
    const payload: Deck = {
      id: crypto.randomUUID(),
      name: name.trim(),
      description: description?.trim() || undefined,
      cards: [],
      createdAt: Date.now()
    }
    if (isLoggedIn.value) {
      const deck = await $fetch<Deck>(`${apiBase}/decks`, {
        method: 'POST',
        headers: authHeaders.value,
        body: payload
      })
      decks.value.push(deck)
      return deck
    }
    decks.value.push(payload)
    persist()
    return payload
  }

  const updateDeck = async (id: string, name: string, description?: string) => {
    const deck = getDeck(id)
    if (!deck) return
    if (isLoggedIn.value) {
      await $fetch(`${apiBase}/decks/${id}`, {
        method: 'PATCH',
        headers: authHeaders.value,
        body: { name: name.trim(), description: description?.trim() || undefined }
      })
    }
    deck.name = name.trim()
    deck.description = description?.trim() || undefined
    if (!isLoggedIn.value) persist()
  }

  const deleteDeck = async (id: string) => {
    if (isLoggedIn.value) {
      await $fetch(`${apiBase}/decks/${id}`, {
        method: 'DELETE',
        headers: authHeaders.value
      })
    }
    const idx = decks.value.findIndex(d => d.id === id)
    if (idx !== -1) {
      decks.value.splice(idx, 1)
      if (!isLoggedIn.value) persist()
    }
  }

  const copyDeck = async (sourceDeckId: string, name: string, description?: string): Promise<Deck> => {
    const deck = await $fetch<Deck>(`${apiBase}/decks/${sourceDeckId}/copy`, {
      method: 'POST',
      headers: authHeaders.value,
      body: {
        name: name.trim(),
        description: description?.trim() || undefined
      }
    })
    decks.value.push({ ...deck, isPinned: false })
    return deck
  }

  const pinDeck = async (sourceDeckId: string): Promise<Deck> => {
    const pinned = await $fetch<{
      id: string
      name: string
      description?: string
      cards: Card[]
      createdAt: number
      owner_id: string
      owner_username: string
      save_count: number
    }>(`${apiBase}/decks/${sourceDeckId}/pin`, {
      method: 'POST',
      headers: authHeaders.value
    })
    const deck: Deck = {
      id: pinned.id,
      name: pinned.name,
      description: pinned.description,
      cards: pinned.cards,
      createdAt: pinned.createdAt,
      ownerId: pinned.owner_id,
      ownerUsername: pinned.owner_username,
      saveCount: pinned.save_count,
      isPinned: true
    }
    pinnedDecks.value.push(deck)
    return deck
  }

  const unpinDeck = async (deckId: string) => {
    await $fetch(`${apiBase}/decks/${deckId}/pin`, {
      method: 'DELETE',
      headers: authHeaders.value
    })
    const idx = pinnedDecks.value.findIndex(d => d.id === deckId)
    if (idx !== -1) pinnedDecks.value.splice(idx, 1)
  }

  // --- Card CRUD ---

  const addCard = async (deckId: string, front: string, back: string): Promise<Card | undefined> => {
    const deck = getDeck(deckId)
    if (!deck) return
    const payload: Card = {
      id: crypto.randomUUID(),
      front: front.trim(),
      back: back.trim(),
      confidence: 0
    }
    if (isLoggedIn.value) {
      const card = await $fetch<Card>(`${apiBase}/decks/${deckId}/cards`, {
        method: 'POST',
        headers: authHeaders.value,
        body: payload
      })
      deck.cards.push(card)
      return card
    }
    deck.cards.push(payload)
    persist()
    return payload
  }

  const updateCard = async (deckId: string, cardId: string, front: string, back: string) => {
    const deck = getDeck(deckId)
    if (!deck) return
    const card = deck.cards.find(c => c.id === cardId)
    if (!card) return
    if (isLoggedIn.value) {
      await $fetch(`${apiBase}/decks/${deckId}/cards/${cardId}`, {
        method: 'PATCH',
        headers: authHeaders.value,
        body: { front: front.trim(), back: back.trim() }
      })
    }
    card.front = front.trim()
    card.back = back.trim()
    if (!isLoggedIn.value) persist()
  }

  const deleteCard = async (deckId: string, cardId: string) => {
    const deck = getDeck(deckId)
    if (!deck) return
    if (isLoggedIn.value) {
      await $fetch(`${apiBase}/decks/${deckId}/cards/${cardId}`, {
        method: 'DELETE',
        headers: authHeaders.value
      })
    }
    deck.cards = deck.cards.filter(c => c.id !== cardId)
    if (!isLoggedIn.value) persist()
  }

  // Confidence and reorder are fire-and-forget for authenticated users (non-critical UX).
  // Local state is updated optimistically before the API call.

  const updateCardConfidence = (deckId: string, cardId: string, confidence: number) => {
    const deck = getDeck(deckId)
    if (!deck) return
    const card = deck.cards.find(c => c.id === cardId)
    if (!card) return
    const clamped = Math.max(0, Math.min(5, confidence))
    card.confidence = clamped
    if (isLoggedIn.value) {
      $fetch(`${apiBase}/decks/${deckId}/cards/${cardId}/confidence`, {
        method: 'PATCH',
        headers: authHeaders.value,
        body: { confidence: clamped }
      }).catch(() => {})
    } else {
      persist()
    }
  }

  const reorderCards = (deckId: string, newOrder: Card[]) => {
    const deck = getDeck(deckId)
    if (!deck) return
    deck.cards = newOrder
    if (isLoggedIn.value) {
      $fetch(`${apiBase}/decks/${deckId}/cards/reorder`, {
        method: 'PATCH',
        headers: authHeaders.value,
        body: { order: newOrder.map(c => c.id) }
      }).catch(() => {})
    } else {
      persist()
    }
  }

  return {
    decks,
    pinnedDecks,
    decksReady,
    markDecksReady,
    getDeck,
    isOwnedDeck,
    isDeckPinned,
    createDeck,
    updateDeck,
    deleteDeck,
    copyDeck,
    pinDeck,
    unpinDeck,
    addCard,
    updateCard,
    updateCardConfidence,
    reorderCards,
    deleteCard,
    loadDecks,
    migrateLocalDecks
  }
}
