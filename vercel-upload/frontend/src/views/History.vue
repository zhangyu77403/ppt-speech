<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, downloadScript } from '../api'
import { notify, store } from '../store'

const router = useRouter()
const decks = ref([])
const scripts = ref([])
const loading = ref(true)
const tab = ref('scripts')

onMounted(load)

async function load() {
  loading.value = true
  try {
    ;[decks.value, scripts.value] = await Promise.all([api.decks(), api.scripts()])
  } catch (e) {
    notify(e.message, 'warn')
  } finally {
    loading.value = false
  }
}

function fmtDate(value) {
  if (!value) return ''
  const d = new Date(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}月${d.getDate()}日 ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function removeScript(item) {
  if (!confirm(`删除讲稿《${item.title}》？`)) return
  await api.removeScript(item.id)
  scripts.value = scripts.value.filter((s) => s.id !== item.id)
  notify('已删除')
}

async function removeDeck(item) {
  if (!confirm(`删除演示文稿《${item.title}》及其讲稿？`)) return
  await api.removeDeck(item.id)
  await load()
  notify('已删除')
}

async function exportAs(item, fmt) {
  try {
    await downloadScript(item, fmt)
  } catch (e) {
    notify(e.message, 'warn')
  }
}
</script>

<template>
  <div class="shell page">
    <div class="spread" style="align-items: flex-end; margin-bottom: 22px">
      <div>
        <p class="eyebrow">归档</p>
        <h1 style="font-size: 32px; margin: 8px 0 6px">我的讲稿</h1>
        <p class="muted small" style="margin: 0">所有生成过的版本都在这里，可随时回到工作台继续修改。</p>
      </div>
      <button class="btn btn-primary" @click="router.push('/')">上传新 PPT</button>
    </div>

    <div class="tabs" style="max-width: 320px">
      <button class="tab" :class="{ active: tab === 'scripts' }" @click="tab = 'scripts'">
        讲稿（{{ scripts.length }}）
      </button>
      <button class="tab" :class="{ active: tab === 'decks' }" @click="tab = 'decks'">
        演示文稿（{{ decks.length }}）
      </button>
    </div>

    <div v-if="loading" class="skeleton" style="height: 160px"></div>

    <template v-else-if="tab === 'scripts'">
      <div v-if="!scripts.length" class="card pad empty">
        <h3>还没有讲稿</h3>
        <p class="small">上传一份 PPT，选好风格就能生成第一份。</p>
      </div>
      <div v-else style="display: grid; gap: 10px">
        <div v-for="item in scripts" :key="item.id" class="deck-card">
          <div class="deck-thumb">稿</div>
          <div style="min-width: 0; flex: 1">
            <div class="row" style="gap: 8px; flex-wrap: wrap">
              <strong style="font-size: 15px">{{ item.title }}</strong>
              <span class="chip chip-accent">{{ item.style_name }}</span>
              <span class="chip">{{ item.word_count }} 字</span>
              <span class="chip">{{ item.duration_min }} 分钟</span>
            </div>
            <div class="small muted" style="margin-top: 2px">
              {{ item.content.slides.length }} 页讲稿 · {{ fmtDate(item.created_at) }} · 听众：{{ item.audience || '—' }}
            </div>
          </div>
          <div class="row" style="gap: 6px">
            <button class="btn btn-ghost" @click="router.push(`/app/${item.presentation_id}`)">编辑</button>
            <button class="btn btn-ink" @click="router.push(`/present/${item.id}`)">演讲</button>
            <button class="btn btn-quiet" @click="exportAs(item, 'docx')">Word</button>
            <button class="btn btn-quiet" @click="removeScript(item)">删除</button>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div v-if="!decks.length" class="card pad empty">
        <h3>还没有上传过 PPT</h3>
        <p class="small">支持 .pptx，单文件不超过 {{ store.config?.max_upload_mb || 30 }}MB。</p>
      </div>
      <div v-else style="display: grid; gap: 10px">
        <div v-for="item in decks" :key="item.id" class="deck-card">
          <div class="deck-thumb">P</div>
          <div style="min-width: 0; flex: 1">
            <strong style="font-size: 15px">{{ item.title }}</strong>
            <div class="small muted" style="margin-top: 2px">
              {{ item.slide_count }} 页 · {{ (item.file_size / 1024).toFixed(0) }} KB · {{ fmtDate(item.created_at) }}
            </div>
          </div>
          <div class="row" style="gap: 6px">
            <button class="btn btn-ghost" @click="router.push(`/app/${item.id}`)">打开</button>
            <button class="btn btn-quiet" @click="removeDeck(item)">删除</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
