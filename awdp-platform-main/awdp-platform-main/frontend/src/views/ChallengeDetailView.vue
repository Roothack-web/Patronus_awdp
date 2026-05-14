<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useChallengeStore } from '../stores/challenges'
import { useContainerStore } from '../stores/container'
import { useAuthStore } from '../stores/auth'
import { api } from '../api'

const route = useRoute()
const challengeStore = useChallengeStore()
const containerStore = useContainerStore()
const auth = useAuthStore()

const flag = ref('')
const submitting = ref(false)
const submitMsg = ref('')
const submitMsgType = ref('')
const operating = ref(false)
const error = ref('')

const detail = computed(() => challengeStore.currentChallenge)
const challenge = computed(() => detail.value?.challenge)
const container = computed(() => detail.value?.container)
const bloods = computed(() => detail.value?.bloods || [])
const submissions = computed(() => detail.value?.submissions || [])
const defenses = computed(() => detail.value?.defenses || [])
const alreadyCorrect = computed(() => detail.value?.already_correct)
const alreadyFixed = computed(() => detail.value?.already_fixed)
const contestEnded = computed(() => detail.value?.contest_ended)

const categoryColor = computed(() => {
  if (!challenge.value) return 'bg-gray-600'
  const colors = { pwn: 'bg-red-600', web: 'bg-blue-600', misc: 'bg-yellow-600', crypto: 'bg-purple-600' }
  return colors[challenge.value.category] || 'bg-gray-600'
})

const bloodIcon = (rank) => {
  if (rank === 1) return '🥇'
  if (rank === 2) return '🥈'
  if (rank === 3) return '🥉'
  return ''
}

async function load() {
  error.value = ''
  try {
    await challengeStore.fetchChallenge(route.params.id)
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)

async function submitFlag() {
  if (!flag.value.trim()) return
  submitting.value = true
  submitMsg.value = ''
  try {
    const result = await challengeStore.submitFlag(route.params.id, flag.value.trim())
    submitMsg.value = result.message || '提交正确！'
    submitMsgType.value = 'success'
    flag.value = ''
    await load()
  } catch (e) {
    submitMsg.value = e.message || 'Flag 不正确'
    submitMsgType.value = 'error'
  } finally {
    submitting.value = false
  }
}

async function startContainer() {
  operating.value = true
  try {
    await containerStore.start(route.params.id)
    await load()
  } catch (e) {
    submitMsg.value = e.message
    submitMsgType.value = 'error'
  } finally {
    operating.value = false
  }
}

async function stopContainer() {
  operating.value = true
  try {
    await containerStore.stop(route.params.id)
    await load()
  } catch (e) {
    submitMsg.value = e.message
    submitMsgType.value = 'error'
  } finally {
    operating.value = false
  }
}

async function resetContainer() {
  if (!confirm('重置容器将清除当前环境，确定继续？')) return
  operating.value = true
  try {
    await containerStore.reset(route.params.id)
    await load()
  } catch (e) {
    submitMsg.value = e.message
    submitMsgType.value = 'error'
  } finally {
    operating.value = false
  }
}

async function refreshFlag() {
  operating.value = true
  try {
    await containerStore.refreshFlag(route.params.id)
    await load()
  } catch (e) {
    submitMsg.value = e.message
    submitMsgType.value = 'error'
  } finally {
    operating.value = false
  }
}

async function downloadSource() {
  try {
    const res = await api.downloadSource(route.params.id)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `challenge-${route.params.id}-source.tar.gz`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    submitMsg.value = '下载失败'
    submitMsgType.value = 'error'
  }
}

function statusBadge(status) {
  if (status === 'running') return { cls: 'bg-green-600', text: '运行中' }
  if (status === 'stopped') return { cls: 'bg-gray-500', text: '已停止' }
  if (status === 'error') return { cls: 'bg-red-600', text: '异常' }
  return { cls: 'bg-yellow-600', text: status }
}
</script>

<template>
  <div v-if="error" class="text-red-400">{{ error }}</div>

  <div v-else-if="!challenge" class="text-gray-400">加载中...</div>

  <template v-else>
    <!-- Title -->
    <div class="flex flex-wrap items-center gap-3 mb-4">
      <h1 class="text-2xl font-bold text-white">{{ challenge.title }}</h1>
      <span class="text-xs font-medium px-2 py-0.5 rounded text-white" :class="categoryColor">
        {{ challenge.category.toUpperCase() }}
      </span>
      <span class="text-sm text-cyan-400">{{ challenge.dynamic_score.toFixed(1) }} 分</span>
    </div>

    <!-- Bloods -->
    <div v-if="bloods.length" class="flex flex-wrap gap-4 mb-4 text-sm">
      <div v-for="b in bloods" :key="b.rank" class="flex items-center gap-1">
        <span>{{ bloodIcon(b.rank) }}</span>
        <span class="font-medium text-gray-200">{{ b.team_name }}</span>
        <span class="text-gray-500">{{ b.time }}</span>
      </div>
    </div>

    <!-- Description -->
    <div class="text-gray-300 mb-6 whitespace-pre-wrap">{{ challenge.description }}</div>

    <!-- Main grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left: 2 columns -->
      <div class="lg:col-span-2 space-y-4">
        <!-- Container card -->
        <div class="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <h3 class="text-lg font-semibold text-white mb-3">靶机容器</h3>

          <template v-if="container">
            <div class="grid grid-cols-2 gap-2 text-sm mb-4">
              <div class="text-gray-400">状态</div>
              <div>
                <span class="text-xs px-2 py-0.5 rounded text-white" :class="statusBadge(container.status).cls">
                  {{ statusBadge(container.status).text }}
                </span>
              </div>
              <div class="text-gray-400">地址</div>
              <div><code class="bg-gray-700 px-1.5 py-0.5 rounded text-cyan-300">{{ container.public_host }}:{{ container.public_port }}</code></div>
              <div class="text-gray-400">Flag 版本</div>
              <div>v{{ container.flag_version }}</div>
              <div class="text-gray-400">重置次数</div>
              <div>{{ container.reset_count }}/{{ container.max_resets }}</div>
            </div>

            <!-- Container actions -->
            <div v-if="contestEnded" class="text-sm text-gray-500 py-2">
              比赛已结束，无法操作容器
            </div>
            <div v-else class="flex flex-wrap gap-2">
              <template v-if="container.status === 'running'">
                <button @click="stopContainer" :disabled="operating" class="bg-yellow-600 hover:bg-yellow-500 disabled:bg-gray-600 text-white text-sm px-3 py-1.5 rounded transition">
                  停止容器
                </button>
                <button @click="resetContainer" :disabled="operating" class="bg-red-700 hover:bg-red-600 disabled:bg-gray-600 text-white text-sm px-3 py-1.5 rounded transition">
                  重置容器
                </button>
                <button @click="refreshFlag" :disabled="operating" class="bg-blue-700 hover:bg-blue-600 disabled:bg-gray-600 text-white text-sm px-3 py-1.5 rounded transition">
                  刷新 Flag
                </button>
              </template>
              <template v-else>
                <button @click="startContainer" :disabled="operating" class="bg-green-600 hover:bg-green-500 disabled:bg-gray-600 text-white text-sm px-3 py-1.5 rounded transition">
                  {{ container.status === 'stopped' ? '启动容器' : '创建并启动容器' }}
                </button>
                <button @click="resetContainer" :disabled="operating" class="bg-red-700 hover:bg-red-600 disabled:bg-gray-600 text-white text-sm px-3 py-1.5 rounded transition">
                  重置容器
                </button>
              </template>
            </div>
          </template>

          <template v-else-if="contestEnded">
            <p class="text-sm text-gray-500">比赛已结束</p>
          </template>
          <template v-else>
            <p class="text-sm text-gray-400 mb-3">尚未创建容器</p>
            <button @click="startContainer" :disabled="operating" class="bg-green-600 hover:bg-green-500 disabled:bg-gray-600 text-white text-sm px-3 py-1.5 rounded transition">
              创建并启动容器
            </button>
          </template>
        </div>

        <!-- Flag submission -->
        <div class="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <h3 class="text-lg font-semibold text-white mb-3">提交 Flag</h3>

          <div v-if="alreadyCorrect" class="bg-green-900/50 border border-green-700 text-green-300 px-4 py-2 rounded text-sm">
            你已正确提交过此题！
          </div>

          <template v-else>
            <div v-if="submitMsg" class="mb-3 px-3 py-2 rounded text-sm" :class="submitMsgType === 'success' ? 'bg-green-900/50 text-green-300 border border-green-700' : 'bg-red-900/50 text-red-300 border border-red-700'">
              {{ submitMsg }}
            </div>

            <form @submit.prevent="submitFlag" class="flex gap-2">
              <input
                v-model="flag"
                type="text"
                class="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500"
                placeholder="输入 Flag 提交"
              />
              <button type="submit" :disabled="submitting" class="bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-600 text-white text-sm px-4 py-2 rounded transition">
                {{ submitting ? '提交中...' : '提交' }}
              </button>
            </form>

            <div class="text-xs text-gray-500 mt-2">
              当前解题队伍: {{ challenge.solve_count || 0 }} |
              当前分值: {{ challenge.dynamic_score.toFixed(1) }}
            </div>
          </template>
        </div>

        <!-- Defense card -->
        <div class="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <h3 class="text-lg font-semibold text-white mb-3">防御 (Fix)</h3>
          <div v-if="alreadyFixed" class="bg-green-900/50 border border-green-700 text-green-300 px-3 py-2 rounded text-sm">
            你已成功修复本题，防御成功！
          </div>
          <template v-else>
            <p class="text-sm text-gray-400 mb-3">下载源码编写补丁，上传修复漏洞获取防御分。</p>
            <div class="flex gap-2">
              <button @click="downloadSource" class="bg-blue-700 hover:bg-blue-600 text-white text-sm px-3 py-1.5 rounded transition">
                下载源码
              </button>
              <router-link :to="`/defend/${challenge.id}`" class="bg-cyan-700 hover:bg-cyan-600 text-white text-sm px-3 py-1.5 rounded transition">
                上传防护包
              </router-link>
            </div>
          </template>
        </div>

        <!-- Submission records -->
        <div v-if="submissions.length" class="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <h3 class="text-lg font-semibold text-white mb-3">最近提交记录</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-gray-400 border-b border-gray-700">
                  <th class="text-left py-2">队伍</th>
                  <th class="text-left py-2">结果</th>
                  <th class="text-left py-2">得分</th>
                  <th class="text-left py-2">时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in submissions.slice(0, 20)" :key="s.id" class="border-b border-gray-700/50">
                  <td class="py-2">{{ s.team_name }}</td>
                  <td class="py-2">
                    <span v-if="s.is_correct" class="bg-green-600 text-white text-xs px-1.5 py-0.5 rounded">正确</span>
                    <span v-else class="bg-gray-600 text-gray-300 text-xs px-1.5 py-0.5 rounded">错误</span>
                  </td>
                  <td class="py-2">{{ s.is_correct ? '+' + s.score_earned.toFixed(1) : '-' }}</td>
                  <td class="py-2 text-gray-500 text-xs">{{ s.submitted_at }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Defense records -->
        <div v-if="defenses.length" class="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <h3 class="text-lg font-semibold text-white mb-3">防护记录</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="text-gray-400 border-b border-gray-700">
                  <th class="text-left py-2">队伍</th>
                  <th class="text-left py-2">状态</th>
                  <th class="text-left py-2">尝试</th>
                  <th class="text-left py-2">时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in defenses" :key="d.id" class="border-b border-gray-700/50">
                  <td class="py-2">{{ d.team_name }}</td>
                  <td class="py-2">
                    <span v-if="d.status === 'success'" class="bg-green-600 text-white text-xs px-1.5 py-0.5 rounded">修复成功</span>
                    <span v-else-if="d.status === 'failed'" class="bg-red-600 text-white text-xs px-1.5 py-0.5 rounded">被攻破</span>
                    <span v-else-if="d.status === 'error'" class="bg-red-600 text-white text-xs px-1.5 py-0.5 rounded">服务异常</span>
                    <span v-else-if="d.status === 'running' || d.status === 'queued'" class="bg-yellow-700 text-yellow-200 text-xs px-1.5 py-0.5 rounded">评估中</span>
                    <span v-else class="bg-gray-600 text-gray-300 text-xs px-1.5 py-0.5 rounded">{{ d.status }}</span>
                  </td>
                  <td class="py-2">{{ d.attempt_number }}</td>
                  <td class="py-2 text-gray-500 text-xs">{{ d.created_at }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Right sidebar -->
      <div class="space-y-4">
        <!-- Score info -->
        <div class="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <h3 class="text-sm font-semibold text-gray-300 mb-3">我的得分</h3>
          <div class="space-y-1 text-sm">
            <div class="flex justify-between"><span class="text-gray-400">攻击分</span><span class="text-cyan-400">{{ auth.teamScore.toFixed(1) }}</span></div>
            <div class="flex justify-between"><span class="text-gray-400">防御分</span><span class="text-yellow-400">{{ (auth.team?.defense_score || 0).toFixed(1) }}</span></div>
            <div class="flex justify-between font-semibold border-t border-gray-700 pt-1 mt-1"><span class="text-white">总分</span><span class="text-white">{{ (auth.team?.score || 0).toFixed(1) }}</span></div>
          </div>
        </div>

        <!-- Stats -->
        <div class="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <h3 class="text-sm font-semibold text-gray-300 mb-3">题目统计</h3>
          <div class="space-y-1 text-sm">
            <div class="flex justify-between"><span class="text-gray-400">解题队伍</span><span>{{ challenge.solve_count || 0 }}</span></div>
            <div class="flex justify-between"><span class="text-gray-400">当前分值</span><span class="text-cyan-400">{{ challenge.dynamic_score.toFixed(1) }}</span></div>
          </div>
        </div>

        <!-- Scoring explanation -->
        <div class="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <h3 class="text-sm font-semibold text-gray-300 mb-3">动态积分说明</h3>
          <p class="text-xs text-gray-400 mb-2">Break 得分 = max(初始分 - (解题数-1) x 递减, 最低分)</p>
          <p class="text-xs text-gray-400 mb-2">前 20 名解出者额外获得排名加成（5% ~ 3.1%）</p>
          <p class="text-xs text-gray-400">Fix 得分 = 每次修复成功获得固定防御分</p>
        </div>
      </div>
    </div>
  </template>
</template>
