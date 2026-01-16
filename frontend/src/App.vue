<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api, { getToken, setToken } from './api'
import type { User } from './types'
import LoginView from './components/LoginView.vue'
import TemplatesGallery from './components/TemplatesGallery.vue'
import ChartConfigurator from './components/ChartConfigurator.vue'
import AdminPanel from './components/AdminPanel.vue'

const user = ref<User | null>(null)
const loadingMe = ref(false)

// 页面模式：'templates' = 模板库, 'template-edit' = 图表配置器, 'admin' = 管理员面板
const pageMode = ref<'templates' | 'template-edit' | 'admin'>('templates')
const activeTemplateId = ref<string | null>(null)

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
  activeTemplateId.value = null
}

function openTemplate(templateId: string) {
  activeTemplateId.value = templateId
  pageMode.value = 'template-edit'
}

function backToGallery() {
  activeTemplateId.value = null
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

  <div v-else class="app-shell">
    <div class="topbar">
      <div class="title">图表模板库</div>
      <div class="nav-tabs">
        <button 
          :class="['nav-tab', { active: pageMode === 'templates' || pageMode === 'template-edit' }]"
          @click="pageMode = 'templates'; activeTemplateId = null"
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

    <!-- 图表配置器 -->
    <ChartConfigurator 
      v-else-if="pageMode === 'template-edit'"
      :template-id="activeTemplateId"
      @back="backToGallery"
    />

    <!-- 管理员面板 -->
    <AdminPanel
      v-else-if="pageMode === 'admin'"
      @back="backFromAdmin"
    />
  </div>
</template>
