<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../api'

interface User {
  id: number
  username: string
  role: 'admin' | 'editor' | 'viewer'
  created_at: string
  last_login_at: string | null
  project_count: number
}

interface Stats {
  total_users: number
  admin_count: number
  editor_count: number
  viewer_count: number
  total_projects: number
  total_versions: number
}

interface Template {
  id: string
  name: string
  category: string
  description: string
  data_files: string[]
  created_at: string | null
}

interface TemplateDetail {
  id: string
  name: string
  category: string
  description: string
  code: string
  data_files: string[]
}

const emit = defineEmits<{
  (e: 'back'): void
}>()

const activeTab = ref<'users' | 'stats' | 'templates'>('templates')
const loading = ref(false)
const error = ref('')

// 统计数据
const stats = ref<Stats | null>(null)

// 用户管理
const users = ref<User[]>([])
const showUserModal = ref(false)
const editingUser = ref<User | null>(null)
const userForm = ref({
  username: '',
  password: '',
  role: 'viewer' as 'admin' | 'editor' | 'viewer'
})

// 模板管理
const templates = ref<Template[]>([])
const categories = ref<string[]>([])
const showTemplateModal = ref(false)
const editingTemplate = ref<TemplateDetail | null>(null)
const templateForm = ref({
  category: '',
  newCategory: '',
  name: '',
  description: '',
  code: '# 在这里编写代码\nimport matplotlib.pyplot as plt\n\nplt.figure(figsize=(10, 6))\nplt.plot([1, 2, 3], [1, 4, 9])\nplt.title(\'示例图表\')\nplt.show()\n'
})
const useNewCategory = ref(false)

const roleLabels: Record<string, string> = {
  admin: '管理员',
  viewer: '只读用户'
}

async function loadStats() {
  try {
    const { data } = await api.get('/admin/stats')
    stats.value = data
  } catch (e: any) {
    console.error('加载统计数据失败:', e)
  }
}

async function loadUsers() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/admin/users')
    users.value = data
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? '加载用户列表失败'
  } finally {
    loading.value = false
  }
}

async function loadTemplates() {
  loading.value = true
  error.value = ''
  try {
    const [templatesRes, categoriesRes] = await Promise.all([
      api.get('/admin/templates'),
      api.get('/admin/templates/categories')
    ])
    templates.value = templatesRes.data
    categories.value = categoriesRes.data
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? '加载模板列表失败'
  } finally {
    loading.value = false
  }
}

function openCreateUser() {
  editingUser.value = null
  userForm.value = { username: '', password: '', role: 'viewer' }
  showUserModal.value = true
}

function openEditUser(user: User) {
  editingUser.value = user
  userForm.value = {
    username: user.username,
    password: '',
    role: user.role
  }
  showUserModal.value = true
}

async function saveUser() {
  error.value = ''
  try {
    if (editingUser.value) {
      // 更新用户
      const payload: any = { role: userForm.value.role }
      if (userForm.value.username !== editingUser.value.username) {
        payload.username = userForm.value.username
      }
      if (userForm.value.password) {
        payload.password = userForm.value.password
      }
      await api.put(`/admin/users/${editingUser.value.id}`, payload)
    } else {
      // 创建用户
      if (!userForm.value.username || !userForm.value.password) {
        error.value = '用户名和密码不能为空'
        return
      }
      await api.post('/admin/users', userForm.value)
    }
    showUserModal.value = false
    loadUsers()
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? '操作失败'
  }
}

async function deleteUser(user: User) {
  if (!confirm(`确定要删除用户 "${user.username}" 吗？此操作不可恢复。`)) {
    return
  }
  try {
    await api.delete(`/admin/users/${user.id}`)
    loadUsers()
  } catch (e: any) {
    alert(e?.response?.data?.detail ?? '删除失败')
  }
}

// 模板管理函数
function openCreateTemplate() {
  editingTemplate.value = null
  useNewCategory.value = categories.value.length === 0
  templateForm.value = {
    category: categories.value[0] || '',
    newCategory: '',
    name: '',
    description: '',
    code: '# 在这里编写代码\nimport matplotlib.pyplot as plt\nimport numpy as np\n\n# 生成数据\nx = np.linspace(0, 10, 100)\ny = np.sin(x)\n\n# 绑定图表\nplt.figure(figsize=(10, 6))\nplt.plot(x, y, \'b-\', linewidth=2)\nplt.title(\'示例图表\')\nplt.xlabel(\'X 轴\')\nplt.ylabel(\'Y 轴\')\nplt.grid(True)\nplt.show()\n'
  }
  showTemplateModal.value = true
}

async function openEditTemplate(template: Template) {
  loading.value = true
  try {
    const { data } = await api.get(`/admin/templates/${template.id}`)
    editingTemplate.value = data
    useNewCategory.value = false
    templateForm.value = {
      category: data.category,
      newCategory: '',
      name: data.name,
      description: data.description,
      code: data.code
    }
    showTemplateModal.value = true
  } catch (e: any) {
    alert(e?.response?.data?.detail ?? '加载模板详情失败')
  } finally {
    loading.value = false
  }
}

async function saveTemplate() {
  error.value = ''
  
  const category = useNewCategory.value ? templateForm.value.newCategory.trim() : templateForm.value.category
  
  if (!category) {
    error.value = '请选择或输入分类'
    return
  }
  if (!templateForm.value.name.trim()) {
    error.value = '请输入模板名称'
    return
  }
  
  try {
    if (editingTemplate.value) {
      // 更新模板
      await api.put(`/admin/templates/${editingTemplate.value.id}`, {
        name: templateForm.value.name.trim(),
        description: templateForm.value.description.trim(),
        code: templateForm.value.code
      })
    } else {
      // 创建模板
      await api.post('/admin/templates', {
        category: category,
        name: templateForm.value.name.trim(),
        description: templateForm.value.description.trim(),
        code: templateForm.value.code
      })
    }
    showTemplateModal.value = false
    loadTemplates()
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? '操作失败'
  }
}

async function deleteTemplate(template: Template) {
  if (!confirm(`确定要删除模板 "${template.name}" 吗？此操作不可恢复。`)) {
    return
  }
  try {
    await api.delete(`/admin/templates/${template.id}`)
    loadTemplates()
  } catch (e: any) {
    alert(e?.response?.data?.detail ?? '删除失败')
  }
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '从未'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadStats()
  loadTemplates()
})
</script>

<template>
  <div class="admin-panel">
    <!-- 顶部返回 -->
    <div class="admin-header">
      <button class="back-btn" @click="$emit('back')">
        ← 返回
      </button>
      <h1>管理员控制面板</h1>
    </div>

    <!-- 标签导航 -->
    <div class="tabs">
      <button
        :class="['tab', { active: activeTab === 'templates' }]"
        @click="activeTab = 'templates'; loadTemplates()"
      >
        📋 模板管理
      </button>
      <button
        :class="['tab', { active: activeTab === 'stats' }]"
        @click="activeTab = 'stats'; loadStats()"
      >
        📊 系统统计
      </button>
      <button
        :class="['tab', { active: activeTab === 'users' }]"
        @click="activeTab = 'users'; loadUsers()"
      >
        👥 用户管理
      </button>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-banner">{{ error }}</div>

    <!-- 统计面板 -->
    <div v-if="activeTab === 'stats'" class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats?.total_users ?? '-' }}</div>
        <div class="stat-label">总用户数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats?.admin_count ?? '-' }}</div>
        <div class="stat-label">管理员</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats?.viewer_count ?? '-' }}</div>
        <div class="stat-label">只读用户</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats?.total_projects ?? '-' }}</div>
        <div class="stat-label">总项目数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats?.total_versions ?? '-' }}</div>
        <div class="stat-label">总版本数</div>
      </div>
    </div>

    <!-- 用户管理 -->
    <div v-if="activeTab === 'users'" class="content-section">
      <div class="section-header">
        <h2>用户列表</h2>
        <button class="btn-primary" @click="openCreateUser">+ 新建用户</button>
      </div>

      <div v-if="loading" class="loading">加载中...</div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>角色</th>
            <th>项目数</th>
            <th>创建时间</th>
            <th>最后登录</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>
              <span :class="['role-badge', user.role]">{{ roleLabels[user.role] }}</span>
            </td>
            <td>{{ user.project_count }}</td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>{{ formatDate(user.last_login_at) }}</td>
            <td>
              <button class="btn-sm" @click="openEditUser(user)">编辑</button>
              <button class="btn-sm btn-danger" @click="deleteUser(user)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 模板管理 -->
    <div v-if="activeTab === 'templates'" class="content-section">
      <div class="section-header">
        <h2>模板库管理</h2>
        <button class="btn-primary" @click="openCreateTemplate">+ 新建模板</button>
      </div>

      <div v-if="loading" class="loading">加载中...</div>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>分类</th>
            <th>模板名称</th>
            <th>描述</th>
            <th>数据文件</th>
            <th>修改时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="template in templates" :key="template.id">
            <td>
              <span class="category-badge">{{ template.category }}</span>
            </td>
            <td>{{ template.name }}</td>
            <td class="desc-cell">{{ template.description || '-' }}</td>
            <td>
              <span v-if="template.data_files.length">
                {{ template.data_files.length }} 个文件
              </span>
              <span v-else class="text-muted">无</span>
            </td>
            <td>{{ formatDate(template.created_at) }}</td>
            <td>
              <button class="btn-sm" @click="openEditTemplate(template)">编辑</button>
              <button class="btn-sm btn-danger" @click="deleteTemplate(template)">删除</button>
            </td>
          </tr>
          <tr v-if="templates.length === 0">
            <td colspan="6" class="empty-row">暂无模板</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 用户编辑弹窗 -->
    <div v-if="showUserModal" class="modal-overlay" @click.self="showUserModal = false">
      <div class="modal">
        <h3>{{ editingUser ? '编辑用户' : '新建用户' }}</h3>
        
        <div class="form-group">
          <label>用户名</label>
          <input
            v-model="userForm.username"
            type="text"
            placeholder="请输入用户名"
          />
        </div>

        <div class="form-group">
          <label>{{ editingUser ? '新密码（留空不修改）' : '密码' }}</label>
          <input
            v-model="userForm.password"
            type="password"
            :placeholder="editingUser ? '留空保持原密码' : '请输入密码'"
          />
        </div>

        <div class="form-group">
          <label>角色</label>
          <select v-model="userForm.role">
            <option value="admin">管理员 - 可管理用户和所有内容</option>
            <option value="viewer">只读用户 - 只能查看内容</option>
          </select>
        </div>

        <div v-if="error" class="form-error">{{ error }}</div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="showUserModal = false">取消</button>
          <button class="btn-primary" @click="saveUser">保存</button>
        </div>
      </div>
    </div>

    <!-- 模板编辑弹窗 -->
    <div v-if="showTemplateModal" class="modal-overlay" @click.self="showTemplateModal = false">
      <div class="modal modal-large">
        <h3>{{ editingTemplate ? '编辑模板' : '新建模板' }}</h3>
        
        <div class="template-form">
          <div class="form-row">
            <div class="form-group" v-if="!editingTemplate">
              <label>分类</label>
              <div class="category-select">
                <select 
                  v-model="templateForm.category" 
                  :disabled="useNewCategory"
                  v-if="categories.length > 0"
                >
                  <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
                </select>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="useNewCategory" />
                  新建分类
                </label>
                <input
                  v-if="useNewCategory"
                  v-model="templateForm.newCategory"
                  type="text"
                  placeholder="输入新分类名称"
                  class="new-category-input"
                />
              </div>
            </div>
            <div class="form-group" v-else>
              <label>分类</label>
              <input type="text" :value="editingTemplate.category" disabled />
            </div>
            
            <div class="form-group">
              <label>模板名称</label>
              <input
                v-model="templateForm.name"
                type="text"
                placeholder="请输入模板名称"
              />
            </div>
          </div>

          <div class="form-group">
            <label>描述</label>
            <textarea
              v-model="templateForm.description"
              placeholder="请输入模板描述"
              rows="2"
            ></textarea>
          </div>

          <div class="form-group code-group">
            <label>代码</label>
            <textarea
              v-model="templateForm.code"
              class="code-editor"
              placeholder="请输入 Python 代码"
              spellcheck="false"
            ></textarea>
          </div>
        </div>

        <div v-if="error" class="form-error">{{ error }}</div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="showTemplateModal = false">取消</button>
          <button class="btn-primary" @click="saveTemplate">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-panel {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px 40px;
}

.admin-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.admin-header h1 {
  margin: 0;
  font-size: 24px;
  color: #1a1a2e;
}

.back-btn {
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f0f0f0;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  background: #fff;
  padding: 8px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.tab {
  padding: 10px 24px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.2s;
}

.tab:hover {
  background: #f5f5f5;
}

.tab.active {
  background: #1a1a2e;
  color: #fff;
}

.error-banner {
  background: #fee2e2;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

.stat-card {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* 内容区域 */
.content-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin: 0;
  font-size: 18px;
  color: #1a1a2e;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* 表格 */
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.data-table th {
  font-weight: 600;
  color: #666;
  font-size: 13px;
  text-transform: uppercase;
}

.data-table td {
  font-size: 14px;
  color: #333;
}

.data-table tr:hover {
  background: #fafafa;
}

.desc-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-row {
  text-align: center;
  color: #999;
  padding: 40px !important;
}

.role-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background: #fee2e2;
  color: #dc2626;
}

.role-badge.editor {
  background: #dbeafe;
  color: #2563eb;
}

.role-badge.viewer {
  background: #f3f4f6;
  color: #666;
}

/* 按钮 */
.btn-primary {
  padding: 10px 20px;
  background: #1a1a2e;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #2d2d44;
}

.btn-secondary {
  padding: 10px 20px;
  background: #f5f5f5;
  color: #333;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #eee;
}

.btn-sm {
  padding: 6px 12px;
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  margin-right: 4px;
  transition: all 0.2s;
}

.btn-sm:hover {
  background: #eee;
}

.btn-danger {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
}

.btn-danger:hover {
  background: #fecaca;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
}

.modal h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #1a1a2e;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #1a1a2e;
}

.form-error {
  color: #dc2626;
  font-size: 13px;
  margin-bottom: 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

/* 模板管理样式 */
.category-badge {
  display: inline-block;
  padding: 4px 10px;
  background: #e0f2fe;
  color: #0369a1;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.text-muted {
  color: #999;
}

.modal-large {
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.template-form {
  margin-bottom: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.category-select {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-select select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
}

.new-category-input {
  margin-top: 4px;
}

.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  resize: vertical;
  font-family: inherit;
}

.form-group textarea:focus {
  outline: none;
  border-color: #1a1a2e;
}

.code-group {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.code-editor {
  flex: 1;
  min-height: 300px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  tab-size: 4;
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 6px;
  padding: 12px;
}

.code-editor:focus {
  outline: none;
  border-color: #3b82f6;
}
</style>





























