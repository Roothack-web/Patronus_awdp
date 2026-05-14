<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useContestStore } from '../stores/contests'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const contestStore = useContestStore()
const auth = useAuthStore()

const error = ref('')
const contest = computed(() => contestStore.currentContest)
const challenges = computed(() => contest.value?.challenges || [])
const rounds = computed(() => contest.value?.rounds || [])

const statusBadge = (status) => {
  if (status === 'running') return { cls: 'bg-green-600', text: '进行中' }
  if (status === 'finished') return { cls: 'bg-gray-600', text: '已结束' }
  return { cls: 'bg-yellow-600', text: '未开始' }
}

const categoryColor = (cat) => {
  const colors = { pwn: 'bg-red-600', web: 'bg-blue-600', misc: 'bg-yellow-600', crypto: 'bg-purple-600' }
  return colors[cat] || 'bg-gray-600'
}

const roundStatusBadge = (status) => {
  if (status === 'running') return { cls: 'bg-green-600', text: '进行中' }
  if (status === 'finished') return { cls: 'bg-gray-600', text: '已结束' }
  return { cls: 'bg-yellow-700 text-yellow-200', text: '待开始' }
}

onMounted(async () => {
  try {
    await contestStore.fetchContest(route.params.id)
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <div>
    <div class="text-sm text-gray-500 mb-3">
      <router-link to="/" class="text-cyan-400 hover:underline">比赛列表</router-link>
      <span class="mx-2">/</span>
      <span class="text-gray-300">{{ contest?.name || '...' }}</span>
    </div>

    <div v-if="error" class="text-red-400">{{ error }}</div>
    <div v-else-if="!contest" class="text-gray-400">加载中...</div>

    <template v-else>
      <div class="flex items-start gap-3 mb-6">
        <div>
          <h1 class="text-2xl font-bold text-white">{{ contest.name }}</h1>
          <span class="text-xs font-medium px-2 py-0.5 rounded text-white inline-block mt-1" :class="statusBadge(contest.status).cls">
            {{ statusBadge(contest.status).text }}
          </span>
          <span v-if="contest.start_at" class="text-sm text-gray-500 ml-3">开始: {{ contest.start_at.slice(0, 16) }}</span>
          <span v-if="contest.end_at" class="text-sm text-gray-500 ml-3">结束: {{ contest.end_at.slice(0, 16) }}</span>
        </div>
      </div>

      <p v-if="contest.description" class="text-gray-400 mb-6">{{ contest.description }}</p>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2">
          <h2 class="text-lg font-semibold text-white mb-4">题目列表</h2>

          <div v-if="!challenges.length" class="text-gray-500 py-8 text-center">
            该比赛暂无可用题目
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <router-link
              v-for="c in challenges"
              :key="c.id"
              :to="`/challenges/${c.id}`"
              class="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-cyan-600 transition group"
            >
              <div class="flex items-start justify-between mb-1">
                <h4 class="text-base font-medium text-white group-hover:text-cyan-400 transition">{{ c.title }}</h4>
                <div class="flex gap-1">
                  <span v-if="c.solved" class="text-xs bg-green-800 text-green-200 px-1.5 py-0.5 rounded">已解</span>
                </div>
              </div>
              <div class="flex items-center gap-2 mt-2">
                <span class="text-xs font-medium px-1.5 py-0.5 rounded text-white" :class="categoryColor(c.category)">
                  {{ c.category.toUpperCase() }}
                </span>
                <span class="text-xs text-gray-500">{{ c.initial_score }} 分</span>
                <span v-if="c.container_status === 'running'" class="text-xs bg-green-700 text-green-200 px-1.5 py-0.5 rounded">运行中</span>
                <span v-else-if="c.container_status === 'stopped'" class="text-xs bg-gray-600 text-gray-300 px-1.5 py-0.5 rounded">已停止</span>
              </div>
              <div class="text-xs text-gray-500 mt-1">{{ c.solve_count }} 队已解</div>
            </router-link>
          </div>
        </div>

        <div>
          <!-- Rounds -->
          <div class="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-4">
            <h3 class="text-sm font-semibold text-gray-300 mb-3">轮次</h3>
            <div v-if="rounds.length">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-gray-500 border-b border-gray-700">
                    <th class="text-left py-1">#</th>
                    <th class="text-left py-1">名称</th>
                    <th class="text-right py-1">状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="r in rounds" :key="r.id" class="border-b border-gray-700/50">
                    <td class="py-1.5 text-gray-400">{{ r.round_number }}</td>
                    <td class="py-1.5 text-gray-300">{{ r.name }}</td>
                    <td class="py-1.5 text-right">
                      <span class="text-xs px-1.5 py-0.5 rounded text-white" :class="roundStatusBadge(r.status).cls">
                        {{ roundStatusBadge(r.status).text }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-else class="text-gray-500 text-sm">暂无轮次</div>
          </div>

          <!-- Actions -->
          <div class="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <h3 class="text-sm font-semibold text-gray-300 mb-3">操作</h3>
            <router-link :to="`/leaderboard?contest_id=${contest.id}`" class="block text-center bg-cyan-700 hover:bg-cyan-600 text-white text-sm px-3 py-1.5 rounded transition">
              查看排行榜
            </router-link>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
