# neydi — frontend

Nuxt 4 app for neydi. Built with Nuxt UI, Vue 3, and TypeScript.

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Dashboard — your decks and pinned decks |
| `/decks/:id` | Manage cards in a deck (owned or pinned) |
| `/study/:id` | Study session with flip cards and confidence tracking |
| `/users` | Browse users |
| `/users/:id` | User profile — decks, followers, copy/pin actions |
| `/login`, `/register` | Authentication |

## Composables

| Composable | Role |
|------------|------|
| `useAuth` | Login, register, JWT session restore, logout |
| `useDecks` | Deck CRUD, pin/copy, card management, guest localStorage + server sync |
| `useFollow` | Follow/unfollow, profile and follower fetching |
| `useTheme` | Dark/light and custom themes (`lahmacun`, `strawberry-shortcake`, `vulnicura`) |

## API proxy

All `/api/**` requests are proxied to the backend (see `nuxt.config.ts`). The browser talks to the same origin; the Nuxt server forwards API calls.

## Guest mode

Unsigned users store decks in `localStorage` under the key `neydi-decks`. On login, `migrateLocalDecks()` pushes them to the server; local data wins on ID conflicts.

## Key components

| Component | Role |
|-----------|------|
| `FlashCard` | Flip card with swipe-to-answer gestures |
| `DraggableList` | Drag-and-drop card reordering |
| `DeckCard` | Deck summary tile on the dashboard |
| `UserSearch` | Header search for finding users |
