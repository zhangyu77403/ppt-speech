import { reactive } from 'vue'
import { api, getToken, setToken } from './api'

export const store = reactive({
  user: null,
  config: null,
  decks: [],
  toast: null,
})

let toastTimer = null

export function notify(text, type = 'ok') {
  store.toast = { text, type, id: Date.now() }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => {
    store.toast = null
  }, 3600)
}

export function isLoggedIn() {
  return Boolean(getToken())
}

export async function login(username, password) {
  const data = await api.login(username, password)
  setToken(data.token)
  store.user = data.user
  return data.user
}

export async function register(payload) {
  const data = await api.register(payload)
  setToken(data.token)
  store.user = data.user
  return data.user
}

export function logout() {
  setToken('')
  store.user = null
  store.decks = []
}

/** 未登录时自动使用体验账号，方便直接试玩。 */
export async function ensureAuth() {
  if (isLoggedIn()) {
    if (!store.user) {
      store.user = await api.me().catch(() => null)
    }
    return Boolean(store.user)
  }
  try {
    await login('demo', 'demo123')
    return true
  } catch {
    return false
  }
}

export async function loadConfig() {
  if (store.config) return store.config
  store.config = await api.config().catch(() => null)
  return store.config
}

export async function loadDecks() {
  if (!isLoggedIn()) return []
  store.decks = await api.decks()
  return store.decks
}
