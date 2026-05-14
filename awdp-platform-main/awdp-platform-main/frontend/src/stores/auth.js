import { defineStore } from 'pinia'
import { api } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    team: null,
    loading: false,
  }),
  getters: {
    isAuthenticated: (state) => !!state.team,
    teamName: (state) => state.team?.name ?? '',
    teamScore: (state) => state.team?.score ?? 0,
  },
  actions: {
    async fetchMe() {
      try {
        const data = await api.me()
        this.team = data.team
      } catch {
        this.team = null
      }
    },
    async login(username, password, remember = false) {
      const data = await api.login(username, password, remember)
      this.team = data.team
    },
    async logout() {
      await api.logout()
      this.team = null
    },
    async register(name, password) {
      await api.register(name, password)
    },
  },
})
