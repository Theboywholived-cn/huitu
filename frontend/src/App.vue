<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api, { getToken, setToken } from './api'
import type { User } from './types'
import LoginView from './components/LoginView.vue'
import TemplatesGallery from './components/TemplatesGallery.vue'
import ChartEditor from './components/ChartEditor.vue'
import AdminPanel from './components/AdminPanel.vue'

interface TemplateMeta {
  id: string
  name: string
  category: string
  tags: string[]
  rel_dir: string
  rel_main: string
  thumbnail?: string
}

const user = ref<User | null>(null)
const loadingMe = ref(false)

// 页面模式：'templates' = 模板库, 'template-edit' = 图表编辑器, 'admin' = 管理员面板
const pageMode = ref<'templates' | 'template-edit' | 'admin'>('templates')
const activeTemplate = ref<TemplateMeta | null>(null)

const isAdmin = computed(() => user.value?.is_admin || user.value?.role === 'admin')

async function fetchMe() {
  if (!getToken()) return
  loadingMe.value = true
  try {
    const { data } = await api.get('/auth/me')
    user.value = data
  } catch {
    setToken(null)
    user.value = null
  } finally {
    loadingMe.value = false
  }
}

function logout() {
  setToken(null)
  user.value = null
  pageMode.value = 'templates'
  activeTemplate.value = null
}

function openTemplate(template: TemplateMeta) {
  activeTemplate.value = template
  pageMode.value = 'template-edit'
}

function backToGallery() {
  activeTemplate.value = null
  pageMode.value = 'templates'
}

function openAdmin() {
  pageMode.value = 'admin'
}

function backFromAdmin() {
  pageMode.value = 'templates'
}

const topRight = computed(() => {
  if (loadingMe.value) return '正在验证...'
  if (!user.value) return ''
  return `${user.value.username} (${user.value.role})`
})

onMounted(fetchMe)
</script>

<template>
  <LoginView v-if="!user" @logged-in="fetchMe" />

  <div v-else-if="pageMode === 'template-edit'" class="editor-fullscreen">
    <!-- 图表编辑器 (全屏模式) -->
    <ChartEditor 
      :template="activeTemplate"
      @back="backToGallery"
    />
  </div>

  <div v-else class="app-shell">
    <div class="topbar">
      <div class="title">图表模板库</div>
      <div class="nav-tabs">
        <button 
          :class="['nav-tab', { active: pageMode === 'templates' }]"
          @click="pageMode = 'templates'; activeTemplate = null"
        >
          📊 模板库
        </button>
        <button 
          v-if="isAdmin"
          :class="['nav-tab admin-tab', { active: pageMode === 'admin' }]"
          @click="openAdmin"
        >
          ⚙️ 管理面板
        </button>
      </div>
      <div style="display:flex; gap:10px; align-items:center;">
        <div style="opacity:0.9;">{{ topRight }}</div>
        <button class="btn" @click="logout">退出</button>
      </div>
    </div>

    <!-- 图表模板库 -->
    <TemplatesGallery 
      v-if="pageMode === 'templates'" 
      @select="openTemplate"
    />

    <!-- 管理员面板 -->
    <AdminPanel
      v-else-if="pageMode === 'admin'"
      @back="backFromAdmin"
    />
  </div>
</template>

<style scoped>
.editor-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
}
</style>










