<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const name = ref('')
const password = ref('')
const confirm = ref('')
const error = ref('')
const submitting = ref(false)

async function handleRegister() {
  if (!name.value || !password.value) {
    error.value = '队伍名和密码不能为空'
    return
  }
  if (password.value.length < 4) {
    error.value = '密码长度至少 4 位'
    return
  }
  if (password.value !== confirm.value) {
    error.value = '两次密码输入不一致'
    return
  }
  error.value = ''
  submitting.value = true
  try {
    await auth.register(name.value, password.value)
    router.push('/login')
  } catch (e) {
    error.value = e.message || '注册失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[70vh]">
    <div class="w-full max-w-sm">
      <div class="bg-gray-800 rounded-lg shadow-lg p-8">
        <h2 class="text-2xl font-bold text-center mb-6 text-cyan-400">队伍注册</h2>

        <form @submit.prevent="handleRegister" class="space-y-4">
          <div v-if="error" class="bg-red-900/50 border border-red-700 text-red-300 px-4 py-2 rounded text-sm">
            {{ error }}
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-1">队伍名</label>
            <input
              v-model="name"
              type="text"
              class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
              placeholder="输入队伍名"
            />
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-1">密码</label>
            <input
              v-model="password"
              type="password"
              class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
              placeholder="输入密码（至少4位）"
            />
          </div>

          <div>
            <label class="block text-sm text-gray-400 mb-1">确认密码</label>
            <input
              v-model="confirm"
              type="password"
              class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
              placeholder="再次输入密码"
            />
          </div>

          <button
            type="submit"
            :disabled="submitting"
            class="w-full bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-600 text-white py-2 rounded font-medium transition"
          >
            {{ submitting ? '注册中...' : '注册' }}
          </button>
        </form>

        <p class="text-center text-sm text-gray-400 mt-4">
          已有队伍？
          <router-link to="/login" class="text-cyan-400 hover:underline">登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>
