# neydi

**Remember more, forget less.**

neydi is a flashcard app for building vocabulary, studying for exams, or memorizing anything worth keeping in your head. Create your own decks, study with a confidence-based system that prioritizes what you still struggle with, and discover decks shared by others — including curated official vocabulary sets.

---

## Features

### Decks & cards

Build flashcard decks with a front and back — words, definitions, questions, anything. Add, edit, reorder, and sort cards by name or confidence. Drag cards into the order that works for you.

### Smart study sessions

Study mode presents cards one at a time with a flip-to-reveal interaction and swipe gestures. After each card you mark **Know** or **Don't Know**, and neydi tracks a confidence score from 0 (new) to 5 (mastered). Cards you struggle with surface more often; cards you've nailed fade into the background.

### Social learning

Every user has a public profile with their decks, follower counts, and discoverability via search. Follow people whose decks you like, browse what they've published, **copy** a deck into your own library, or **pin** it to your dashboard to study without making a full copy.

### Official decks

Curated starter decks — like German A1, A2, and B1 vocabulary — ship with the app and are maintained by the neydi team. Copy them, pin them, or use them as templates for your own learning path.

### Works without an account

Try neydi as a guest: decks are saved locally in your browser. When you sign up, your guest decks migrate to your account automatically.

### Themes

Switch between dark and light mode, or pick a custom theme. Study in whatever mood suits you.

---

## Tech stack

| Layer | Stack |
|-------|-------|
| Frontend | Nuxt 4, Nuxt UI 4, Vue 3, TypeScript, Tailwind CSS 4 |
| Backend | FastAPI, SQLAlchemy (async), PostgreSQL |
| Auth | JWT bearer tokens, bcrypt password hashing |

---

## Project structure

```
neydi/
├── neydi-fe/    # Nuxt frontend
├── neydi-be/    # FastAPI backend
└── scripts/     # Stack launchers
```

See also:

- [Frontend (`neydi-fe`)](./neydi-fe/README.md)
- [Backend (`neydi-be`)](./neydi-be/README.md)
