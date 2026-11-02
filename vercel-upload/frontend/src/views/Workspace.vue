<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, downloadScript } from '../api'
import { notify } from '../store'

const route = useRoute()
const router = useRouter()

const deck = ref(null)
const styles = ref([])
const script = ref(null)
const loading = ref(true)
const generating = ref(false)
const saving = ref(false)
const savedLabel = ref('')
const activeSlide = ref(0)

const form = reactive({
  style_key: 'formal',
  duration_min: 8,
  audience: '公司同事',
  language: 'zh',
  extra: '',
})

const selectedStyle = computed(() => styles.value.find((s) => s.key === form.style_key))
const durationPct = computed(() => `${((form.duration_min - 1) / 29) * 100}%`)

onMounted(async () => {
  try {
    const [d, s] = await Promise.all([api.deck(route.params.id), api.styles()])
    deck.value = d
    styles.value = s
    const existing = await api.scripts(d.id).catch(() => [])
    if (existing.length) {
      script.value = existing[0]
      Object.assign(form, {
        style_key: existing[0].style_key,
        duration_min: existing[0].duration_min,
        audience: existing[0].audience,
        language: existing[0].language,
      })
      await nextTick()
      resizeAll()
    }
  } catch (e) {
    notify(e.message || '加载失败', 'warn')
    router.replace('/')
  } finally {
    loading.value = false
  }
})

async function generate() {
  if (!deck.value) return
  generating.value = true
  savedLabel.value = ''
  try {
    const result = await api.generate({
      presentation_id: deck.value.id,
      style_key: form.style_key,
      duration_min: form.duration_min,
      audience: form.audience || '听众',
      language: form.language,
      extra: form.extra,
    })
    script.value = result
    await nextTick()
    resizeAll()
    window.scrollTo({ top: 0, behavior: 'smooth' })
    notify(`已按「${result.style_name}」生成 ${result.content.slides.length} 页讲稿`)
  } catch (e) {
    notify(e.message || '生成失败', 'warn')
  } finally {
    generating.value = false
  }
}

async function save() {
  if (!script.value) return
  saving.value = true
  try {
    const updated = await api.updateScript(script.value.id, { content: script.value.content })
    script.value = updated
    await nextTick()
    resizeAll()
    savedLabel.value = '已保存'
    setTimeout(() => {
      if (savedLabel.value === '已保存') savedLabel.value = ''
    }, 2400)
  } catch (e) {
    notify(e.message || '保存失败', 'warn')
  } finally {
    saving.value = false
  }
}

function resize(el) {
  if (!el || el.tagName !== 'TEXTAREA') return
  el.style.height = 'auto'
  el.style.height = `${el.scrollHeight}px`
}

function resizeAll() {
  document.querySelectorAll('textarea.script-text').forEach(resize)
}

const vAutosize = {
  mounted: (el) => nextTick(() => resize(el)),
  updated: (el) => nextTick(() => resize(el)),
}

function goSection(index) {
  activeSlide.value = index
  document.getElementById(`sec-${index}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function fullText() {
  if (!script.value) return ''
  const c = script.value.content
  const parts = [`# ${script.value.title}`, '', '## 开场白', c.opening, '']
  for (const s of c.slides) parts.push(`## 第 ${s.index} 页 · ${s.title}`, '', s.script, '')
  parts.push('## 结束语', c.closing)
  return parts.join('\n')
}

async function copyAll() {
  try {
    await navigator.clipboard.writeText(fullText())
    notify('全文已复制到剪贴板')
  } catch {
    notify('复制失败，请手动选择文本', 'warn')
  }
}

async function exportAs(fmt) {
  try {
    await downloadScript(script.value, fmt)
    notify(fmt === 'docx' ? 'Word 已开始下载' : 'Markdown 已开始下载')
  } catch (e) {
    notify(e.message, 'warn')
  }
}

function fmtTime(seconds) {
  const s = Math.max(0, Number(seconds) || 0)
  return `${Math.floor(s / 60)}分${String(s % 60).padStart(2, '0')}秒`
}
</script>

<template>
  <div class="shell page">
    <div v-if="loading" style="display: grid; gap: 14px">
      <div class="skeleton" style="height: 40px; width: 40%"></div>
      <div class="skeleton" style="height: 220px"></div>
    </div>

    <template v-else-if="deck">
      <div class="script-head">
        <div>
          <p class="eyebrow">工作台</p>
          <h1 style="font-size: 32px; margin: 8px 0 10px">{{ deck.title }}</h1>
          <div class="row small muted" style="gap: 8px; flex-wrap: wrap">
            <span class="chip">{{ deck.slide_count }} 页</span>
            <span class="chip">{{ deck.original_filename }}</span>
            <span v-if="script" class="chip chip-accent">{{ script.style_name }}</span>
            <span v-if="script" class="chip">{{ script.word_count }} 字 · 约 {{ script.duration_min }} 分钟</span>
            <span v-if="script" class="chip chip-green">
              {{ script.engine === 'llm' ? 'AI 生成' : '模板引擎' }}
            </span>
          </div>
        </div>
        <div class="row" style="gap: 8px">
          <button v-if="script" class="btn btn-ghost" @click="copyAll">复制全文</button>
          <button v-if="script" class="btn btn-ghost" @click="exportAs('md')">导出 .md</button>
          <button v-if="script" class="btn btn-ink" @click="router.push(`/present/${script.id}`)">进入演讲模式</button>
        </div>
      </div>

      <div class="workspace">
        <!-- 左：页目录 -->
        <aside class="side">
          <p class="side-title">幻灯片</p>
          <div
            v-for="s in deck.slides"
            :key="s.slide_index"
            class="slide-item"
            :class="{ active: activeSlide === s.slide_index }"
            @click="goSection(s.slide_index)"
          >
            <span class="slide-no">{{ String(s.slide_index).padStart(2, '0') }}</span>
            <span class="slide-name">{{ s.title }}</span>
          </div>
        </aside>

        <!-- 中：讲稿 -->
        <section>
          <div v-if="!script" class="card pad empty">
            <h3>还没有讲稿</h3>
            <p class="small" style="max-width: 420px; margin: 0 auto 18px">
              在右侧选择一种风格、设定时长和听众，点「生成讲稿」，我会把 {{ deck.slide_count }} 页内容写成可以照着念的话。
            </p>
            <button class="btn btn-primary" :disabled="generating" @click="generate">
              {{ generating ? '正在生成…' : '生成讲稿' }}
            </button>
          </div>

          <template v-else>
            <div class="script-card">
              <div class="sec-label">
                <span class="sec-no">开场</span>
                <span class="sec-title">开场白</span>
                <span class="small muted" style="margin-left: auto">{{ script.content.opening.length }} 字</span>
              </div>
              <textarea
                v-autosize
                v-model="script.content.opening"
                class="script-text editable"
                spellcheck="false"
                @blur="save"
              ></textarea>
            </div>

            <div
              v-for="item in script.content.slides"
              :id="`sec-${item.index}`"
              :key="item.index"
              class="script-card"
            >
              <div class="sec-label">
                <span class="sec-no">第 {{ String(item.index).padStart(2, '0') }} 页</span>
                <span class="sec-title">{{ item.title }}</span>
                <span class="small muted" style="margin-left: auto">{{ fmtTime(item.seconds) }}</span>
              </div>
              <textarea
                v-autosize
                v-model="item.script"
                class="script-text editable"
                spellcheck="false"
                @blur="save"
              ></textarea>
              <div class="sec-meta">
                <span>{{ item.script.length }} 字</span>
                <span>建议用时 {{ fmtTime(item.seconds) }}</span>
                <span v-if="deck.slides[item.index - 1]?.body?.length">
                  原页要点 {{ deck.slides[item.index - 1].body.length }} 条
                </span>
              </div>
            </div>

            <div class="script-card">
              <div class="sec-label">
                <span class="sec-no">结尾</span>
                <span class="sec-title">结束语</span>
              </div>
              <textarea
                v-autosize
                v-model="script.content.closing"
                class="script-text editable"
                spellcheck="false"
                @blur="save"
              ></textarea>
            </div>

            <div v-if="script.content.tips?.length" class="script-card" style="background: #fbf7ee">
              <div class="sec-label">
                <span class="sec-no">提示</span>
                <span class="sec-title">现场提示</span>
              </div>
              <ul style="margin: 6px 0 0; padding-left: 20px; color: var(--ink-2)">
                <li v-for="(tip, i) in script.content.tips" :key="i" style="margin-bottom: 6px">{{ tip }}</li>
              </ul>
            </div>
          </template>
        </section>

        <!-- 右：设置 -->
        <aside class="panel card">
          <div class="panel-head">
            <div class="spread">
              <h3 style="font-size: 16px">生成设置</h3>
              <span v-if="savedLabel" class="chip chip-green small">{{ savedLabel }}</span>
            </div>
            <p class="small muted" style="margin: 6px 0 0">换风格可重新生成，不会覆盖已有记录</p>
          </div>

          <div class="panel-body">
            <div class="field">
              <label>演讲风格</label>
              <div class="style-grid">
                <button
                  v-for="s in styles"
                  :key="s.key"
                  class="style-card"
                  :class="{ active: form.style_key === s.key }"
                  :title="s.description"
                  @click="form.style_key = s.key"
                >
                  <span class="name"><span>{{ s.emoji }}</span>{{ s.name }}</span>
                  <span class="tag">{{ s.tagline }}</span>
                </button>
              </div>
            </div>

            <div class="field">
              <label class="spread" style="display: flex">
                <span>目标时长</span>
                <span class="mono" style="color: var(--ink)">{{ form.duration_min }} 分钟</span>
              </label>
              <input
                v-model.number="form.duration_min"
                class="range"
                type="range"
                min="1"
                max="30"
                step="1"
                :style="{ '--pct': durationPct }"
              />
              <p class="small muted" style="margin: 0">
                约 {{ form.duration_min * 240 }} 字，按每分钟 240 字估算
              </p>
            </div>

            <div class="field">
              <label>听众</label>
              <input v-model.trim="form.audience" class="input" placeholder="公司同事 / 评委老师 / 投资人" />
            </div>

            <div class="field">
              <label>语言</label>
              <select v-model="form.language" class="input">
                <option value="zh">中文</option>
                <option value="en">English</option>
              </select>
            </div>

            <div class="field" style="margin-bottom: 0">
              <label>额外要求（可选）</label>
              <textarea
                v-model.trim="form.extra"
                class="input"
                rows="2"
                placeholder="例如：多讲一个团队故事；不要提融资"
              ></textarea>
            </div>
          </div>

          <div class="panel-foot">
            <button class="btn btn-primary btn-block" :disabled="generating" @click="generate">
              <span v-if="generating">正在生成<span class="dots"></span></span>
              <span v-else>{{ script ? '按当前设置重新生成' : '生成讲稿' }}</span>
            </button>
            <div v-if="script" class="row" style="margin-top: 10px; gap: 8px">
              <button class="btn btn-ghost" style="flex: 1" @click="exportAs('docx')">Word</button>
              <button class="btn btn-ghost" style="flex: 1" @click="router.push(`/present/${script.id}`)">演讲模式</button>
            </div>
            <p v-if="selectedStyle" class="small muted" style="margin: 12px 0 0; line-height: 1.6">
              {{ selectedStyle.description }}
            </p>
            <p v-if="saving" class="small muted" style="margin: 8px 0 0">保存中…</p>
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>
