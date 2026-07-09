export interface UserPublicResponse {
  id: string
  username: string
  created_at: string
}

export interface UserProfileResponse extends UserPublicResponse {
  followers_count: number
  following_count: number
}

export interface FollowStatusResponse {
  is_following: boolean
}

export const useFollow = () => {
  const { public: { apiBase } } = useRuntimeConfig()
  const { token } = useAuth()

  const authHeaders = computed(() => ({
    Authorization: `Bearer ${token.value}`
  }))

  const getProfile = async (userId: string): Promise<UserProfileResponse> => {
    return await $fetch<UserProfileResponse>(`${apiBase}/users/${userId}`)
  }

  const getFollowStatus = async (userId: string): Promise<FollowStatusResponse> => {
    return await $fetch<FollowStatusResponse>(`${apiBase}/users/${userId}/follow-status`, {
      headers: authHeaders.value
    })
  }

  const toggleFollow = async (userId: string): Promise<FollowStatusResponse> => {
    return await $fetch<FollowStatusResponse>(`${apiBase}/users/${userId}/follow`, {
      method: 'POST',
      headers: authHeaders.value
    })
  }

  const getFollowers = async (userId: string, skip = 0, limit = 20): Promise<UserPublicResponse[]> => {
    return await $fetch<UserPublicResponse[]>(`${apiBase}/users/${userId}/followers`, {
      params: { skip, limit }
    })
  }

  return {
    getProfile,
    getFollowStatus,
    toggleFollow,
    getFollowers
  }
}
