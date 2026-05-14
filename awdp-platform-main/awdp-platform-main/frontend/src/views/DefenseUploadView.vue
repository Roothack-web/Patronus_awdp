<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const router = useRouter()

const challenge = ref(null)
const alreadyFixed = ref(false)
const file = ref(null)
const submitting = ref(false)
const message = ref('')
const msgType = ref('')
const attemptCount = ref(0)
const maxAttempts = ref(10)

onMounted(async () => {
  try {
    const data = await api.getDefenseUpload(route.params.id)
    challenge.value = data
    attemptCount.value = data.attempt_count
    maxAttempts.value = data.max_attempts
    alreadyFixed.value = data.is_fixed || false
  } catch (e) {
    message.value = e.message
    msgType.value = 'error'
  }
})

function onFileSelected(e) {
  file.value = e.target.files[0]
}

async function handleUpload() {
  if (!file.value) {
    message.value = '请选择防护包文件'
    msgType.value = 'error'
    return
  }
  submitting.value = true
  message.value = ''
  const formData = new FormData()
  formData.append('package', file.value)
  try {
    const result = await api.uploadDefense(route.params.id, formData)
    message.value = result.message || '上传成功'
    msgType.value = 'success'
    attemptCount.value = result.attempt_number
    setTimeout(() => router.push(`/challenges/${route.params.id}`), 2000)
  } catch (e) {
    message.value = e.message
    msgType.value = 'error'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="max-w-lg mx-auto">
    <div class="bg-gray-800 border border-gray-700 rounded-lg p-6">
      <h2 class="text-xl font-bold text-white mb-2">上传防护包</h2>
      <p v-if="challenge" class="text-sm text-gray-400 mb-6">
        题目: {{ challenge.challenge_title }}
        (第 {{ attemptCount + 1 }}/{{ maxAttempts }} 次)
      </p>

      <div v-if="message" class="mb-4 px-3 py-2 rounded text-sm" :class="msgType === 'success' ? 'bg-green-900/50 text-green-300 border border-green-700' : 'bg-red-900/50 text-red-300 border border-red-700'">
        {{ message }}
      </div>

      <form @submit.prevent="handleUpload" class="space-y-4">
        <div class="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center hover:border-cyan-500 transition">
          <input
            type="file"
            accept=".tar.gz,.tgz,.tar"
            @change="onFileSelected"
            class="w-full text-sm text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0 file:bg-cyan-600 file:text-white hover:file:bg-cyan-500"
          />
          <p v-if="file" class="text-sm text-gray-300 mt-2">{{ file.name }} ({{ (file.size / 1024).toFixed(1) }} KB)</p>
          <p v-else class="text-xs text-gray-500 mt-2">支持 tar.gz 格式，需包含 update.sh</p>
        </div>

        <button
          type="submit"
          :disabled="submitting || challenge?.is_fixed"
          class="w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-600 text-white py-2 rounded font-medium transition"
        >
          {{ submitting ? '上传中...' : '上传防护包' }}
        </button>
      </form>

      <div class="mt-4 text-center">
        <router-link :to="`/challenges/${route.params.id}`" class="text-sm text-cyan-400 hover:underline">
          返回题目详情
        </router-link>
      </div>
    </div>
  </div>
</template>
