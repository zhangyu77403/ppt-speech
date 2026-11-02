<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from './api'
import { store, login, logout, loadConfig, isLoggedIn } from './store'

const route = useRoute()
const router = useRouter()

onMounted(async () => {
  await loadConfig()
  if (isLoggedIn() && !store.user) {
    store.user = await api.me().catch(() => null)
  }
})

function initial(name) {
  return (name || '客').slice(0, 1)
}

async function quickLogin() {
  try {
    await login('demo', 'demo123')
    router.push('/history')
  } catch (e) {
    /* 由页面提示 */
  }
}
</script>

<template>
  <div v-if="route.meta.bare">
    <router-view />
  </div>
  <div v-else>
    <header class="nav">
      <div class="shell nav-inner">
        <router-link to="/" class="brand">
          <span class="seal">讲</span>
          <span>讲稿工坊</span>
        </router-link>
        <nav class="nav-links">
          <router-link class="nav-link" to="/">开始制作</router-link>
          <router-link v-if="store.user" class="nav-link" to="/history">我的讲稿</router-link>
        </nav>
        <div class="nav-right">
          <span v-if="store.config" class="chip chip-green small" :title="'数据库：' + store.config.db_backend">
            {{ store.config.llm_enabled ? 'AI 生成' : '模板引擎' }}
          </span>
          <template v-if="store.user">
            <div class="row" style="gap: 8px">
              <div class="avatar">{{ initial(store.user.display_name || store.user.username) }}</div>
              <span class="small muted">{{ store.user.display_name || store.user.username }}</span>
            </div>
            <button class="btn btn-quiet" @click="logout(); router.push('/')">退出</button>
          </template>
          <template v-else>
            <button class="btn btn-ghost" @click="router.push('/login')">登录</button>
            <button class="btn btn-primary" @click="quickLogin">体验一下</button>
          </template>
        </div>
      </div>
    </header>

    <main>
      <router-view />
    </main>

    <transition name="fade">
      <div v-if="store.toast" class="toast" :class="store.toast.type">{{ store.toast.text }}</div>
    </transition>
  </div>
</template>
