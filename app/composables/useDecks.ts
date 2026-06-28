const STORAGE_KEY = 'neydi-decks'

export interface Card {
  id: string
  front: string
  back: string
}

export interface Deck {
  id: string
  name: string
  description?: string
  cards: Card[]
  createdAt: number
}

export const useDecks = () => {
  const decks = useState<Deck[]>('decks', () => {
    if (import.meta.client) {
      try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) return JSON.parse(stored) as Deck[]
      } catch {}
    }
    return []
  })

  const persist = () => {
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(decks.value))
    }
  }

  const getDeck = (id: string): Deck | undefined =>
    decks.value.find(d => d.id === id)

  const createDeck = (name: string, description?: string): Deck => {
    const deck: Deck = {
      id: crypto.randomUUID(),
      name: name.trim(),
      description: description?.trim() || undefined,
      cards: [],
      createdAt: Date.now()
    }
    decks.value.push(deck)
    persist()
    return deck
  }

  const updateDeck = (id: string, name: string, description?: string) => {
    const deck = getDeck(id)
    if (!deck) return
    deck.name = name.trim()
    deck.description = description?.trim() || undefined
    persist()
  }

  const deleteDeck = (id: string) => {
    const idx = decks.value.findIndex(d => d.id === id)
    if (idx !== -1) {
      decks.value.splice(idx, 1)
      persist()
    }
  }

  const addCard = (deckId: string, front: string, back: string): Card | undefined => {
    const deck = getDeck(deckId)
    if (!deck) return
    const card: Card = {
      id: crypto.randomUUID(),
      front: front.trim(),
      back: back.trim()
    }
    deck.cards.push(card)
    persist()
    return card
  }

  const updateCard = (deckId: string, cardId: string, front: string, back: string) => {
    const deck = getDeck(deckId)
    if (!deck) return
    const card = deck.cards.find(c => c.id === cardId)
    if (!card) return
    card.front = front.trim()
    card.back = back.trim()
    persist()
  }

  const deleteCard = (deckId: string, cardId: string) => {
    const deck = getDeck(deckId)
    if (!deck) return
    deck.cards = deck.cards.filter(c => c.id !== cardId)
    persist()
  }

  return {
    decks,
    getDeck,
    createDeck,
    updateDeck,
    deleteDeck,
    addCard,
    updateCard,
    deleteCard
  }
}
