<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { store, ensureAuth, isLoggedIn, loadDecks, notify } from '../store'

const route = useRoute()
const router = useRouter()
const uploading = ref(false)
const over = ref(false)
const fileInput = ref(null)
const styles = ref([])

onMounted(async () => {
  styles.value = await api.styles().catch(() => [])
  if (route.query.demo === '1') {
    await trySample()
    return
  }
  if (isLoggedIn()) {
    await loadDecks().catch(() => {})
  }
})

const recent = computed(() => store.decks.slice(0, 3))
const maxMb = computed(() => store.config?.max_upload_mb || 30)

function pick() {
  fileInput.value?.click()
}

async function onFile(file) {
  if (!file) return
  if (!/\.pptx$/i.test(file.name)) {
    notify('只支持 .pptx 文件，可先用 PowerPoint 另存为 pptx', 'warn')
    return
  }
  if (file.size > maxMb.value * 1024 * 1024) {
    notify(`文件 ${(file.size / 1024 / 1024).toFixed(1)}MB，超过上限 ${maxMb.value}MB`, 'warn')
    return
  }
  uploading.value = true
  try {
    if (!(await ensureAuth())) {
      notify('请先登录', 'warn')
      router.push('/login')
      return
    }
    const deck = await api.upload(file)
    notify(`已解析《${deck.title}》，共 ${deck.slide_count} 页`)
    router.push(`/app/${deck.id}`)
  } catch (e) {
    notify(e.message || '上传失败', 'warn')
  } finally {
    uploading.value = false
  }
}

function onDrop(e) {
  over.value = false
  onFile(e.dataTransfer?.files?.[0])
}

async function onChange(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  await onFile(file)
}

async function trySample() {
  if (!(await ensureAuth())) return router.push('/login')
  const decks = await loadDecks().catch(() => [])
  if (!decks.length) return notify('还没有示例文稿', 'warn')
  router.push(`/app/${decks[0].id}`)
}
</script>

<template>
  <div class="shell" style="padding-top: 56px; padding-bottom: 90px">
    <div style="display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 54px; align-items: center">
      <div>
        <p class="eyebrow">PPT → 演讲稿</p>
        <h1 style="font-size: 46px; margin: 14px 0 18px; letter-spacing: -0.01em">
          把 PPT，<br />变成一份能直接念的讲稿。
        </h1>
        <p class="muted" style="font-size: 16px; max-width: 460px; line-height: 1.9">
          上传你的 .pptx，选一种演讲风格。开场白、逐页过渡、结尾呼吁，都会按你的时长和听众写好——不是摘要，是能照着念的话。
        </p>
        <div class="row" style="margin-top: 28px; gap: 10px; flex-wrap: wrap">
          <button class="btn btn-primary btn-lg" @click="pick">上传 PPT 开始</button>
          <button class="btn btn-ghost btn-lg" @click="trySample">看看示例</button>
        </div>
        <div class="row small muted" style="margin-top: 18px; gap: 18px; flex-wrap: wrap">
          <span>· 支持 .pptx</span>
          <span>· 单文件 ≤ {{ maxMb }}MB</span>
          <span>· 可导出 Word / Markdown</span>
        </div>
      </div>

      <div>
        <div
          class="drop"
          :class="{ over }"
          @click="pick"
          @dragover.prevent="over = true"
          @dragleave.prevent="over = false"
          @drop.prevent="onDrop"
        >
          <div v-if="uploading">
            <div class="drop-icon">⏳</div>
            <div class="drop-title">正在解析幻灯片<span class="dots"></span></div>
            <p class="small muted">提取标题、要点与备注</p>
          </div>
          <template v-else>
            <div class="drop-icon">📄</div>
            <div class="drop-title">把 PPT 拖到这里</div>
            <p class="small muted">或点击选择文件 · 只支持 .pptx</p>
            <div style="margin-top: 20px">
              <span class="chip">解析标题 · 要点 · 备注</span>
            </div>
          </template>
        </div>
        <input ref="fileInput" type="file" accept=".pptx" hidden @change="onChange" />

        <div v-if="recent.length" style="margin-top: 18px">
          <p class="side-title">最近打开</p>
          <div style="display: grid; gap: 8px">
            <router-link
              v-for="deck in recent"
              :key="deck.id"
              :to="`/app/${deck.id}`"
              class="deck-card"
              style="padding: 10px 12px"
            >
              <div class="deck-thumb" style="width: 34px; height: 34px; font-size: 13px">稿</div>
              <div style="min-width: 0">
                <div style="font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">
                  {{ deck.title }}
                </div>
                <div class="small muted">{{ deck.slide_count }} 页</div>
              </div>
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <section style="margin-top: 96px">
      <div class="spread" style="align-items: flex-end; margin-bottom: 20px">
        <div>
          <p class="eyebrow">风格</p>
          <h2 style="font-size: 26px; margin-top: 8px">八种风格，同一份 PPT 讲出不同的味道</h2>
        </div>
        <span class="small muted">生成时可随时切换重写</span>
      </div>
      <div class="style-grid" style="grid-template-columns: repeat(4, minmax(0, 1fr))">
        <div v-for="s in styles" :key="s.key" class="style-card" style="cursor: default">
          <div class="name"><span>{{ s.emoji }}</span>{{ s.name }}</div>
          <div class="tag">{{ s.tagline }}</div>
        </div>
      </div>
    </section>

    <section style="margin-top: 78px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px">
      <div class="card pad">
        <div class="sec-no" style="width: fit-content">01</div>
        <h3 style="margin: 12px 0 8px; font-size: 18px">上传即解析</h3>
        <p class="small muted" style="margin: 0">
          逐页提取标题、要点和演讲者备注，表格也会被读成要点，不需要手动整理。
        </p>
      </div>
      <div class="card pad">
        <div class="sec-no" style="width: fit-content">02</div>
        <h3 style="margin: 12px 0 8px; font-size: 18px">按时长控字数</h3>
        <p class="small muted" style="margin: 0">
          选定 5 分钟还是 20 分钟，每页写多少字、讲多久，都会按语速自动分配。
        </p>
      </div>
      <div class="card pad">
        <div class="sec-no" style="width: fit-content">03</div>
        <h3 style="margin: 12px 0 8px; font-size: 18px">上台就能用</h3>
        <p class="small muted" style="margin: 0">
          全屏演讲模式带计时器和提词器，讲完一键导出 Word 或 Markdown。
        </p>
      </div>
    </section>
  </div>
</template>
