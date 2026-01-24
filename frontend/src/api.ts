import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 180000
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const status = err?.response?.status
    if (status === 401) {
      localStorage.removeItem('token')
    }
    return Promise.reject(err)
  }
)

export function setToken(token: string | null) {
  if (!token) localStorage.removeItem('token')
  else localStorage.setItem('token', token)
}

export function getToken(): string | null {
  return localStorage.getItem('token')
}

// =====================================================
// Templates API (Phase 3)
// =====================================================

export interface TemplateMeta {
  id: string
  name: string
  category: string
  tags: string[]
  rel_dir: string
  rel_main: string
  thumbnail: string | null
}

export interface TemplateTreeNode {
  name: string
  path: string
  type: 'folder' | 'template'
  children: TemplateTreeNode[]
  template_id?: string
}

export interface TemplatesListResponse {
  root: string
  templates: TemplateMeta[]
  tree: TemplateTreeNode
}

/**
 * Fetch structured templates list from backend
 */
export async function fetchTemplates(): Promise<TemplatesListResponse> {
  const { data } = await api.get<TemplatesListResponse>('/templates/list')
  return data
}

/**
 * Fetch flat templates list (backward compatible)
 */
export async function fetchTemplatesFlat(): Promise<TemplateMeta[]> {
  const { data } = await api.get<TemplateMeta[]>('/templates')
  return data
}

/**
 * Run a template with uploaded data file(s).
 * Returns a Blob (PNG image) on success.
 */
export async function runTemplate(templateId: string, file: File): Promise<Blob> {
  const formData = new FormData()
  formData.append('template_id', templateId)
  formData.append('files', file)

  const response = await api.post('/templates/run', formData, {
    responseType: 'blob',
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  // Check if response is an error (JSON) masquerading as blob
  const contentType = response.headers['content-type'] || ''
  if (contentType.includes('application/json')) {
    // Parse error from blob
    const text = await response.data.text()
    const err = JSON.parse(text)
    throw new Error(err.detail || 'Template execution failed')
  }

  return response.data as Blob
}

export default api
