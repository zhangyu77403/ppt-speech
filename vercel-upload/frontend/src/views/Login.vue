<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login, register, notify } from '../store'

const route = useRoute()
const router = useRouter()

const mode = ref('login')
const form = reactive({ username: '', password: '', display_name: '' })
const loading = ref(false)

async function submit() {
  if (!form.username || !form.password) return notify('请填写用户名和密码', 'warn')
  loading.value = true
  try {
    if (mode.value === 'login') await login(form.username, form.password)
    else await register({ ...form, display_name: form.display_name || form.username })
    notify('欢迎回来')
    router.push(route.query.next || '/')
  } catch (e) {
    notify(e.message || '操作失败', 'warn')
  } finally {
    loading.value = false
  }
}

async function demo() {
  loading.value = true
  try {
    await login('demo', 'demo123')
    router.push(route.query.next || '/')
  } catch (e) {
    notify(e.message, 'warn')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-wrap">
    <aside class="auth-side">
      <router-link to="/" class="brand" style="color: #f2e9dc">
        <span class="seal">讲</span>
        <span>讲稿工坊</span>
      </router-link>
      <div class="auth-quote">
        “演讲不是把 PPT 念一遍，<br />而是把话说到人心里。”
      </div>
      <div class="small" style="color: #a89a8b; position: relative; z-index: 1">
        Vue 3 · FastAPI · MySQL ｜ 上传 PPT，生成逐页讲稿
      </div>
    </aside>

    <main class="auth-main">
      <div class="auth-card">
        <div class="tabs">
          <button class="tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
          <button class="tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
        </div>

        <h2 style="font-size: 26px; margin-bottom: 6px">
          {{ mode === 'login' ? '继续你的讲稿' : '创建一个账号' }}
        </h2>
        <p class="small muted" style="margin-top: 0; margin-bottom: 24px">
          {{ mode === 'login' ? '登录后可管理所有演示文稿与历史讲稿' : '注册后即可上传 PPT 并保存讲稿' }}
        </p>

        <form @submit.prevent="submit">
          <div class="field">
            <label>用户名</label>
            <input v-model.trim="form.username" class="input" autocomplete="username" placeholder="例如 zhangsan" />
          </div>
          <div v-if="mode === 'register'" class="field">
            <label>显示名称（可选）</label>
            <input v-model.trim="form.display_name" class="input" placeholder="张三" />
          </div>
          <div class="field">
            <label>密码</label>
            <input
              v-model="form.password"
              class="input"
              type="password"
              autocomplete="current-password"
              placeholder="至少 6 位"
            />
          </div>

          <button class="btn btn-primary btn-block btn-lg" type="submit" :disabled="loading" style="margin-top: 8px">
            {{ loading ? '处理中…' : mode === 'login' ? '登录' : '注册并登录' }}
          </button>
        </form>

        <div style="margin: 22px 0; display: flex; align-items: center; gap: 12px" class="small muted">
          <span style="flex: 1; height: 1px; background: var(--line)"></span>
          或者
          <span style="flex: 1; height: 1px; background: var(--line)"></span>
        </div>

        <button class="btn btn-ghost btn-block" :disabled="loading" @click="demo">使用体验账号（demo / demo123）</button>

        <p class="small muted" style="margin-top: 24px">
          <router-link to="/" style="text-decoration: underline">← 返回首页</router-link>
        </p>
      </div>
    </main>
  </div>
</template>
