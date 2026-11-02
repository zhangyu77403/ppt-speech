<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { notify } from '../store'

const route = useRoute()
const router = useRouter()

const script = ref(null)
const index = ref(0)
const seconds = ref(0)
const paused = ref(false)
let timer = null

const sections = computed(() => {
  if (!script.value) return []
  const c = script.value.content
  return [
    { kind: 'open', label: '开场白', title: script.value.title, text: c.opening, seconds: 0 },
    ...c.slides.map((s) => ({
      kind: 'slide',
      label: `第 ${s.index} 页`,
      title: s.title,
      text: s.script,
      seconds: s.seconds,
    })),
    { kind: 'close', label: '结束语', title: '结束语', text: c.closing, seconds: 0 },
  ]
})

const current = computed(() => sections.value[index.value])
const progress = computed(() =>
  sections.value.length ? ((index.value + 1) / sections.value.length) * 100 : 0
)
const next = computed(() => sections.value[index.value + 1])

onMounted(async () => {
  try {
    script.value = await api.script(route.params.id)
    document.title = `${script.value.title} · 演讲模式`
  } catch (e) {
    notify(e.message, 'warn')
    router.replace('/')
  }
  timer = setInterval(() => {
    if (!paused.value) seconds.value += 1
  }, 1000)
  window.addEventListener('keydown', onKey)
})

onBeforeUnmount(() => {
  clearInterval(timer)
  window.removeEventListener('keydown', onKey)
  document.title = '讲稿工坊 · 把 PPT 变成能直接念的演讲稿'
})

function onKey(e) {
  if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) {
    e.preventDefault()
    nextSlide()
  } else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) {
    e.preventDefault()
    prevSlide()
  } else if (e.key === 'Escape') {
    router.back()
  } else if (e.key.toLowerCase() === 'p') {
    paused.value = !paused.value
  } else if (e.key.toLowerCase() === 'f') {
    toggleFullscreen()
  }
}

function nextSlide() {
  if (index.value < sections.value.length - 1) index.value += 1
}

function prevSlide() {
  if (index.value > 0) index.value -= 1
}

async function toggleFullscreen() {
  try {
    if (!document.fullscreenElement) await document.documentElement.requestFullscreen()
    else await document.exitFullscreen()
  } catch {
    /* 浏览器可能拒绝 */
  }
}

const clock = computed(() => {
  const m = String(Math.floor(seconds.value / 60)).padStart(2, '0')
  const s = String(seconds.value % 60).padStart(2, '0')
  return `${m}:${s}`
})

const speed = computed(() => {
  if (!script.value) return '—'
  return `${script.value.word_count} 字 · 目标 ${script.value.duration_min} 分钟`
})
</script>

<template>
  <div v-if="script" class="present">
    <div class="present-top">
      <div class="row" style="gap: 14px">
        <button class="btn btn-quiet" style="color: #c8b8a8" @click="router.back()">← 退出</button>
        <span>{{ script.title }}</span>
        <span class="chip" style="background: rgba(246,239,229,0.1); color: #c8b8a8">
          {{ script.style_name }} · 目标 {{ script.duration_min }} 分钟
        </span>
      </div>
      <div class="row" style="gap: 18px">
        <button class="btn btn-quiet" style="color: #c8b8a8" @click="paused = !paused">
          {{ paused ? '继续' : '暂停' }}
        </button>
        <button class="btn btn-quiet" style="color: #c8b8a8" @click="toggleFullscreen">全屏</button>
        <span class="mono" style="color: #a08e7d">{{ speed }}</span>
        <span class="timer">{{ clock }}</span>
      </div>
    </div>

    <div class="present-body">
      <div>
        <div class="row" style="gap: 10px; color: #a08e7d; font-size: 13px; letter-spacing: 0.14em">
          <span>{{ current.label }}</span>
          <span>{{ index + 1 }} / {{ sections.length }}</span>
        </div>
        <h1 class="present-title">{{ current.title }}</h1>
        <p class="present-script">{{ current.text }}</p>
      </div>

      <aside class="present-notes">
        <h4>提示</h4>
        <ul style="margin: 0 0 26px; padding-left: 18px">
          <li v-for="(tip, i) in script.content.tips" :key="i">{{ tip }}</li>
          <li v-if="!script.content.tips?.length">按 → 翻页，按 P 暂停计时，按 F 全屏</li>
        </ul>

        <div v-if="next">
          <h4>下一页</h4>
          <div style="font-family: var(--serif); font-size: 18px; color: #e6d9c9; margin-bottom: 6px">
            {{ next.title }}
          </div>
          <div style="font-size: 13px; line-height: 1.9; color: #9d8c7b; max-height: 120px; overflow: hidden">
            {{ next.text.slice(0, 90) }}{{ next.text.length > 90 ? '…' : '' }}
          </div>
        </div>
        <div v-else>
          <h4>最后一页</h4>
          <div style="font-size: 14px; color: #9d8c7b">讲完这一页，向听众致谢并留出提问时间。</div>
        </div>
      </aside>
    </div>

    <div class="present-foot">
      <span>← → 翻页</span>
      <div class="progress"><i :style="{ width: progress + '%' }"></i></div>
      <span>P 暂停 · F 全屏 · Esc 退出</span>
    </div>
  </div>
</template>
