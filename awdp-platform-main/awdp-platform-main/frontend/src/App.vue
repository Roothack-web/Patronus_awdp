<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const mobileMenuOpen = ref(false)

const navLinks = [
  { name: '比赛', path: '/' },
  { name: '排行榜', path: '/leaderboard' },
]

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

onMounted(() => {
  auth.fetchMe()
})
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-gray-100">
    <!-- Navbar -->
    <nav class="bg-gray-800 border-b border-gray-700">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center gap-8">
            <router-link to="/" class="text-xl font-bold text-cyan-400 tracking-wide">
              AWDP
            </router-link>
            <div class="hidden md:flex gap-6">
              <router-link
                v-for="link in navLinks"
                :key="link.path"
                :to="link.path"
                class="text-sm text-gray-300 hover:text-white transition"
                :class="{ 'text-cyan-400': route.path === link.path }"
              >
                {{ link.name }}
              </router-link>
            </div>
          </div>
          <div class="hidden md:flex items-center gap-4">
            <template v-if="auth.isAuthenticated">
              <span class="text-sm text-gray-400">
                {{ auth.teamName }}
                <span class="text-cyan-400 ml-1">{{ auth.teamScore.toFixed(1) }}分</span>
              </span>
              <button @click="handleLogout" class="text-sm text-gray-400 hover:text-red-400 transition">
                退出
              </button>
            </template>
            <template v-else>
              <router-link to="/login" class="text-sm text-gray-300 hover:text-white transition">登录</router-link>
              <router-link to="/register" class="text-sm text-gray-300 hover:text-white transition">注册</router-link>
            </template>
          </div>
          <!-- Mobile menu button -->
          <button @click="mobileMenuOpen = !mobileMenuOpen" class="md:hidden text-gray-300">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>
      <!-- Mobile menu -->
      <div v-if="mobileMenuOpen" class="md:hidden border-t border-gray-700 px-4 py-3 space-y-2">
        <router-link v-for="link in navLinks" :key="link.path" :to="link.path" class="block text-sm text-gray-300 py-1" @click="mobileMenuOpen = false">
          {{ link.name }}
        </router-link>
        <template v-if="auth.isAuthenticated">
          <div class="text-sm text-gray-400 py-1">{{ auth.teamName }} ({{ auth.teamScore.toFixed(1) }}分)</div>
          <button @click="handleLogout" class="text-sm text-red-400 py-1">退出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="block text-sm text-gray-300 py-1">登录</router-link>
          <router-link to="/register" class="block text-sm text-gray-300 py-1">注册</router-link>
        </template>
      </div>
    </nav>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <router-view />
    </main>
  </div>
</template>
