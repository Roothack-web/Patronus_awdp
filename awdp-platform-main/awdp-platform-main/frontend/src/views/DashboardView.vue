<script setup>
import { ref, onMounted, computed } from 'vue'
import { useContestStore } from '../stores/contests'
import { useAuthStore } from '../stores/auth'

const contestStore = useContestStore()
const auth = useAuthStore()

onMounted(() => {
  contestStore.fetchContests()
})

const statusColor = (status) => {
  if (status === 'running') return 'bg-green-600'
  if (status === 'finished') return 'bg-gray-600'
  return 'bg-yellow-600'
}

const statusText = (status) => {
  if (status === 'running') return '进行中'
  if (status === 'finished') return '已结束'
  return '未开始'
}

const now = ref(Date.now())
setInterval(() => { now.value = Date.now() }, 1000)

function formatRemaining(seconds) {
  if (!seconds || seconds <= 0) return ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}
</script>

<template>
  <div>
    <div class="text-center py-4 mb-6">
      <h1 class="text-4xl font-bold text-cyan-400 mb-2">砺剑 AWDp</h1>
      <p class="text-gray-400">Attack With Defense Plus — 砺剑铸盾，攻防制胜</p>
    </div>

    <div v-if="contestStore.loading" class="text-gray-400 text-center py-8">加载中...</div>

    <template v-else-if="contestStore.contests.length">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <router-link
          v-for="c in contestStore.contests"
          :key="c.id"
          :to="`/contests/${c.id}`"
          class="bg-gray-800 border border-gray-700 rounded-lg p-5 hover:border-cyan-600 transition group"
        >
          <div class="flex items-start justify-between mb-2">
            <h3 class="text-lg font-semibold text-white group-hover:text-cyan-400 transition">{{ c.name }}</h3>
            <span class="text-xs font-medium px-2 py-0.5 rounded text-white" :class="statusColor(c.status)">
              {{ statusText(c.status) }}
            </span>
          </div>
          <p v-if="c.description" class="text-sm text-gray-400 mb-3">{{ c.description.slice(0, 200) }}</p>
          <div class="flex items-center gap-4 text-xs text-gray-500">
            <span>{{ c.challenge_count }} 道题目</span>
            <span v-if="c.start_at">开始: {{ c.start_at.slice(5, 16) }}</span>
            <span v-if="c.end_at">结束: {{ c.end_at.slice(5, 16) }}</span>
          </div>
          <div v-if="c.status === 'running' && c.remaining_seconds > 0" class="mt-2 text-sm text-cyan-400 font-mono">
            剩余 {{ formatRemaining(c.remaining_seconds) }}
          </div>
        </router-link>
      </div>
    </template>

    <div v-else class="text-center py-12">
      <p class="text-gray-500 text-lg mb-4">暂无可用比赛</p>
      <div class="flex justify-center gap-3">
        <router-link to="/leaderboard" class="bg-gray-700 hover:bg-gray-600 text-gray-200 px-4 py-2 rounded transition text-sm">
          查看排行榜
        </router-link>
      </div>
    </div>
  </div>
</template>
