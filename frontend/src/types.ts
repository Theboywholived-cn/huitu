export type User = {
  id: number
  username: string
  role: 'admin' | 'viewer'
  is_admin: boolean
}

export type Project = {
  id: number
  name: string
  description: string
  created_at: string
  updated_at: string
}

export type ProjectDetail = Project & {
  latest_version_id?: number | null
  latest_option_text?: string | null
}

export type Version = {
  id: number
  project_id: number
  created_by: number
  comment: string
  option_text: string
  created_at: string
}
















