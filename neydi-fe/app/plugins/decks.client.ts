const STORAGE_KEY = 'neydi-decks'

export default defineNuxtPlugin(() => {
  // Authenticated users get their decks from the server via loadDecks() in app.vue.
  // Hydrating from localStorage for them would cause a flash of stale data.
  if (localStorage.getItem('auth:token')) return

  const decks = useState('decks')
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) decks.value = JSON.parse(stored)
  } catch { }

  useState('decksReady', () => false).value = true
})
