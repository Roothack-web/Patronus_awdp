import { defineStore } from 'pinia'
import { api } from '../api'

export const useContestStore = defineStore('contests', {
  state: () => ({
    contests: [],
    currentContest: null,
    loading: false,
  }),
  actions: {
    async fetchContests() {
      this.loading = true
      try {
        this.contests = await api.contests()
      } finally {
        this.loading = false
      }
    },
    async fetchContest(id) {
      this.loading = true
      try {
        this.currentContest = await api.contestDetail(id)
      } finally {
        this.loading = false
      }
    },
    clearCurrent() {
      this.currentContest = null
    },
  },
})
