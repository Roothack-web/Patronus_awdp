import { defineStore } from 'pinia'
import { api } from '../api'

export const useContainerStore = defineStore('container', {
  state: () => ({
    operating: false,
  }),
  actions: {
    async start(challengeId) {
      this.operating = true
      try {
        return await api.startContainer(challengeId)
      } finally {
        this.operating = false
      }
    },
    async stop(challengeId) {
      this.operating = true
      try {
        return await api.stopContainer(challengeId)
      } finally {
        this.operating = false
      }
    },
    async reset(challengeId) {
      this.operating = true
      try {
        return await api.resetContainer(challengeId)
      } finally {
        this.operating = false
      }
    },
    async refreshFlag(challengeId) {
      this.operating = true
      try {
        return await api.refreshFlag(challengeId)
      } finally {
        this.operating = false
      }
    },
  },
})
