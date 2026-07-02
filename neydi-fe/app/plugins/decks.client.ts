const STORAGE_KEY = 'neydi-decks'

export default defineNuxtPlugin(() => {
  const decks = useState('decks')
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) decks.value = JSON.parse(stored)
  } catch { }
})
