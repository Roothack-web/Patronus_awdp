<script setup>
import { ref, onMounted } from 'vue'
import { useLeaderboardStore } from '../stores/leaderboard'

const store = useLeaderboardStore()
const loading = ref(true)

onMounted(async () => {
  await store.fetch()
  loading.value = false
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-white mb-6">排行榜</h1>

    <div v-if="store.frozen" class="bg-yellow-900/50 border border-yellow-700 text-yellow-300 px-3 py-2 rounded text-sm mb-4">
      排行榜已冻结，将在 {{ store.freezeUntil }} 解冻
    </div>

    <div v-if="loading" class="text-gray-400">加载中...</div>

    <div v-else class="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-700/50 text-gray-300">
              <th class="text-left px-4 py-3">排名</th>
              <th class="text-left px-4 py-3">队伍</th>
              <th class="text-right px-4 py-3">攻击分</th>
              <th class="text-right px-4 py-3">防御分</th>
              <th class="text-right px-4 py-3">总分</th>
              <th class="text-right px-4 py-3">解题数</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(r, i) in store.rows"
              :key="i"
              class="border-t border-gray-700/50 hover:bg-gray-700/30 transition"
            >
              <td class="px-4 py-3">
                <span
                  class="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold"
                  :class="{
                    'bg-yellow-600 text-white': r.rank === 1,
                    'bg-gray-400 text-gray-800': r.rank === 2,
                    'bg-amber-700 text-white': r.rank === 3,
                    'text-gray-400': r.rank > 3,
                  }"
                >
                  {{ r.rank }}
                </span>
              </td>
              <td class="px-4 py-3 font-medium text-white">{{ r.team_name }}</td>
              <td class="px-4 py-3 text-right text-cyan-400">{{ r.attack_score.toFixed(1) }}</td>
              <td class="px-4 py-3 text-right text-yellow-400">{{ r.defense_score.toFixed(1) }}</td>
              <td class="px-4 py-3 text-right font-semibold text-white">{{ r.score.toFixed(1) }}</td>
              <td class="px-4 py-3 text-right text-gray-400">{{ r.solved }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!store.rows.length" class="text-center text-gray-500 py-8">
        暂无数据
      </div>
    </div>
  </div>
</template>
