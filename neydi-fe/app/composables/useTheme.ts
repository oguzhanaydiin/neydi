export type Theme = 'dark' | 'light' | 'lahmacun' | 'strawberry-shortcake' | 'vulnicura'

export const CUSTOM_THEMES: Theme[] = ['lahmacun', 'strawberry-shortcake', 'vulnicura']

export function useTheme() {
  const colorMode = useColorMode()
  const themePref = useCookie<Theme>('neydi-theme', {
    default: () => 'dark',
    sameSite: 'lax'
  })

  function setTheme(t: Theme) {
    themePref.value = t
    const darkThemes: Theme[] = ['dark', 'vulnicura']
    colorMode.preference = darkThemes.includes(t) ? 'dark' : 'light'

    if (import.meta.client) {
      if (CUSTOM_THEMES.includes(t)) {
        document.documentElement.dataset.theme = t
      } else {
        delete document.documentElement.dataset.theme
      }
    }
  }

  return {
    theme: readonly(themePref),
    setTheme
  }
}
