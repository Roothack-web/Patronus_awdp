import { defineStore } from 'pinia'
import { api } from '../api'

export const useChallengeStore = defineStore('challenges', {
  state: () => ({
    challenges: [],
    currentChallenge: null,
    loading: false,
  }),
  actions: {
    async fetchChallenges() {
      this.loading = true
      try {
        this.challenges = await api.challenges()
      } finally {
        this.loading = false
      }
    },
    async fetchChallenge(id) {
      this.loading = true
      try {
        this.currentChallenge = await api.challengeDetail(id)
      } finally {
        this.loading = false
      }
    },
    async submitFlag(challengeId, flag) {
      return await api.submitFlag(challengeId, flag)
    },
    clearCurrent() {
      this.currentChallenge = null
    },
  },
})
