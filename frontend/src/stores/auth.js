import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi } from '@/api/auth'
import { getUserProfile } from '@/api/users'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)

  const isLoggedIn = computed(() => !!token.value)
  const creditLevel = computed(() => user.value?.credit_level || 'good')
  const creditScore = computed(() => user.value?.credit_score || 100)

  function setAuth(access, refresh) {
    token.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function clearAuth() {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  async function login(credentials) {
    const res = await loginApi(credentials)
    const data = res.data.data || res.data
    setAuth(data.access, data.refresh)
    await fetchProfile()
    return data
  }

  async function register(form) {
    const res = await registerApi(form)
    return res.data
  }

  async function fetchProfile() {
    if (!token.value) return
    try {
      const res = await getUserProfile()
      user.value = res.data.data || res.data
    } catch {
      clearAuth()
    }
  }

  async function checkAuth() {
    if (token.value) {
      await fetchProfile()
    }
  }

  function logout() {
    clearAuth()
    window.location.href = '/login'
  }

  return {
    user,
    token,
    refreshToken,
    isLoggedIn,
    creditLevel,
    creditScore,
    login,
    register,
    logout,
    fetchProfile,
    checkAuth,
    setAuth,
    clearAuth,
  }
})
