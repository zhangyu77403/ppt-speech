const TOKEN_KEY = 'ss_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

async function request(path, { method = 'GET', body, form } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  let payload
  if (form) {
    payload = form
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  const res = await fetch(`/api${path}`, { method, headers, body: payload })
  if (!res.ok) {
    let message = `请求失败（${res.status}）`
    try {
      const data = await res.json()
      if (typeof data.detail === 'string') message = data.detail
      else if (Array.isArray(data.detail)) message = data.detail.map((d) => d.msg).join('；')
    } catch {
      /* 忽略非 JSON 响应 */
    }
    throw new Error(message)
  }
  const type = res.headers.get('content-type') || ''
  if (type.includes('application/json')) return res.json()
  return res.text()
}

export const api = {
  login: (username, password) => request('/auth/login', { method: 'POST', body: { username, password } }),
  register: (payload) => request('/auth/register', { method: 'POST', body: payload }),
  me: () => request('/auth/me'),
  config: () => request('/meta/config'),
  styles: () => request('/styles'),

  decks: () => request('/presentations'),
  deck: (id) => request(`/presentations/${id}`),
  removeDeck: (id) => request(`/presentations/${id}`, { method: 'DELETE' }),
  upload: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/presentations/upload', { method: 'POST', form })
  },

  generate: (payload) => request('/scripts/generate', { method: 'POST', body: payload }),
  scripts: (presentationId) =>
    request(`/scripts${presentationId ? `?presentation_id=${presentationId}` : ''}`),
  script: (id) => request(`/scripts/${id}`),
  updateScript: (id, payload) => request(`/scripts/${id}`, { method: 'PATCH', body: payload }),
  removeScript: (id) => request(`/scripts/${id}`, { method: 'DELETE' }),
}

export async function downloadScript(script, fmt) {
  const res = await fetch(`/api/scripts/${script.id}/export?fmt=${fmt}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  })
  if (!res.ok) throw new Error('导出失败')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${script.title || '演讲稿'}.${fmt}`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
