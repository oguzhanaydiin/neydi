export interface RegisterPayload {
  email: string
  username: string
  password: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface UserResponse {
  id: string
  email: string
  username: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export const useAuth = () => {
  const { public: { apiBase } } = useRuntimeConfig()

  const user = useState<UserResponse | null>('auth:user', () => null)
  // NOTE: don't read localStorage in the useState initializer. On the client the
  // initializer isn't re-run during hydration (the value is restored from the SSR
  // payload as null), so the token would always be lost on refresh. It's hydrated
  // from localStorage in restoreSession() instead, which runs client-side onMounted.
  const token = useState<string | null>('auth:token', () => null)

  const isLoggedIn = computed(() => !!token.value)

  const register = async (payload: RegisterPayload): Promise<UserResponse> => {
    return await $fetch<UserResponse>(`${apiBase}/auth/register`, {
      method: 'POST',
      body: payload
    })
  }

  const login = async (payload: LoginPayload): Promise<void> => {
    const data = await $fetch<{ access_token: string }>(`${apiBase}/auth/token`, {
      method: 'POST',
      // OAuth2PasswordRequestForm expects form data, not JSON
      body: new URLSearchParams({
        username: payload.email,
        password: payload.password
      }),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    token.value = data.access_token
    if (import.meta.client) {
      localStorage.setItem('auth:token', data.access_token)
    }

    // fetch and cache the user profile
    user.value = await $fetch<UserResponse>(`${apiBase}/auth/me`, {
      headers: { Authorization: `Bearer ${data.access_token}` }
    })
  }

  const logout = () => {
    user.value = null
    token.value = null
    if (import.meta.client) {
      localStorage.removeItem('auth:token')
    }
    navigateTo('/login')
  }

  // Restore user from stored token on page refresh
  const restoreSession = async () => {
    // Hydrate token from localStorage on the client (see note above).
    if (import.meta.client && !token.value) {
      token.value = localStorage.getItem('auth:token')
    }
    if (!token.value || user.value) return
    try {
      user.value = await $fetch<UserResponse>(`${apiBase}/auth/me`, {
        headers: { Authorization: `Bearer ${token.value}` }
      })
    } catch {
      // token is expired or invalid - clear it
      token.value = null
      if (import.meta.client) localStorage.removeItem('auth:token')
    }
  }

  return {
    user,
    token,
    isLoggedIn,
    register,
    login,
    logout,
    restoreSession
  }
}
