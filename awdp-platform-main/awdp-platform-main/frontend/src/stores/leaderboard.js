import { defineStore } from 'pinia'
import { api } from '../api'

export const useLeaderboardStore = defineStore('leaderboard', {
  state: () => ({
    rows: [],
    frozen: false,
    freezeUntil: null,
    loading: false,
  }),
  actions: {
    async fetch(contestId) {
      this.loading = true
      try {
        const data = await api.leaderboard(contestId)
        this.rows = data.rows
        this.frozen = data.frozen
        this.freezeUntil = data.freeze_until
      } finally {
        this.loading = false
      }
    },
  },
})
