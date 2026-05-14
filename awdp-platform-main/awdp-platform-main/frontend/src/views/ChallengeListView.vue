<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const groups = ref([])
const ungrouped = ref([])
const loading = ref(true)

const categoryColor = (cat) => {
  const colors = { pwn: 'bg-red-600', web: 'bg-blue-600', misc: 'bg-yellow-600', crypto: 'bg-purple-600' }
  return colors[cat] || 'bg-gray-600'
}

onMounted(async () => {
  try {
    const [allChallenges, allContests] = await Promise.all([
      api.challenges(),
      api.contests(),
    ])

    // Build contest map
    const contestMap = {}
    for (const c of allContests) {
      contestMap[c.id] = c
    }

    // Group challenges by contest_id
    const grouped = {}
    const ungroupedList = []
    for (const ch of allChallenges) {
      if (ch.contest_id) {
        if (!grouped[ch.contest_id]) {
          grouped[ch.contest_id] = { contest: contestMap[ch.contest_id], challenges: [] }
        }
        grouped[ch.contest_id].challenges.push(ch)
      } else {
        ungroupedList.push(ch)
      }
    }

    groups.value = Object.values(grouped)
    ungrouped.value = ungroupedList
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-white mb-6">题目列表</h1>

    <div v-if="loading" class="text-gray-400">加载中...</div>

    <template v-else>
      <!-- Contest groups -->
      <div v-for="g in groups" :key="g.contest.id" class="bg-gray-800 border border-gray-700 rounded-lg mb-4 overflow-hidden">
        <div class="px-5 py-3 border-b border-gray-700 flex items-center justify-between">
          <div>
            <router-link :to="`/contests/${g.contest.id}`" class="text-lg font-semibold text-white hover:text-cyan-400 transition">
              {{ g.contest.name }}
            </router-link>
          </div>
          <span v-if="g.contest.status === 'running'" class="text-xs bg-green-600 text-white px-2 py-0.5 rounded">进行中</span>
          <span v-else-if="g.contest.status === 'finished'" class="text-xs bg-gray-600 text-white px-2 py-0.5 rounded">已结束</span>
          <span v-else class="text-xs bg-yellow-600 text-white px-2 py-0.5 rounded">未开始</span>
        </div>
        <div class="p-4">
          <div v-if="!g.challenges.length" class="text-gray-500 text-sm">该比赛暂无题目</div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <router-link
              v-for="c in g.challenges"
              :key="c.id"
              :to="`/challenges/${c.id}`"
              class="bg-gray-700/50 border border-gray-600 rounded-lg p-4 hover:border-cyan-600 transition group"
            >
              <div class="flex items-start justify-between mb-1">
                <h4 class="text-base font-medium text-white group-hover:text-cyan-400 transition">{{ c.title }}</h4>
                <div class="flex gap-1 shrink-0">
                  <span v-if="c.solved" class="text-xs bg-green-800 text-green-200 px-1.5 py-0.5 rounded">已解</span>
                </div>
              </div>
              <div class="flex items-center gap-2 mt-2">
                <span class="text-xs font-medium px-1.5 py-0.5 rounded text-white" :class="categoryColor(c.category)">
                  {{ c.category.toUpperCase() }}
                </span>
                <span class="text-xs text-cyan-400">{{ c.dynamic_score.toFixed(1) }} 分</span>
                <span class="text-xs text-gray-500 ml-auto">{{ c.solve_count }} 队已解</span>
              </div>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Ungrouped challenges (admin only) -->
      <div v-if="ungrouped.length" class="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <div class="px-5 py-3 border-b border-gray-700">
          <h3 class="text-lg font-semibold text-gray-300">未分组题目</h3>
        </div>
        <div class="p-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <router-link
              v-for="c in ungrouped"
              :key="c.id"
              :to="`/challenges/${c.id}`"
              class="bg-gray-700/50 border border-gray-600 rounded-lg p-4 hover:border-cyan-600 transition group"
            >
              <div class="flex items-start justify-between mb-1">
                <h4 class="text-base font-medium text-white group-hover:text-cyan-400 transition">{{ c.title }}</h4>
                <div class="flex gap-1 shrink-0">
                  <span v-if="c.solved" class="text-xs bg-green-800 text-green-200 px-1.5 py-0.5 rounded">已解</span>
                </div>
              </div>
              <div class="flex items-center gap-2 mt-2">
                <span class="text-xs font-medium px-1.5 py-0.5 rounded text-white" :class="categoryColor(c.category)">
                  {{ c.category.toUpperCase() }}
                </span>
                <span class="text-xs text-cyan-400">{{ c.dynamic_score.toFixed(1) }} 分</span>
                <span class="text-xs text-gray-500 ml-auto">{{ c.solve_count }} 队已解</span>
              </div>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!groups.length && !ungrouped.length" class="text-center py-12">
        <p class="text-gray-500">暂无可用题目</p>
      </div>
    </template>
  </div>
</template>
