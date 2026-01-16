<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import api from '../api'

interface TemplateInfo {
  id: string
  name: string
  category: string
  description: string
  thumbnail: string | null
  has_data_file: boolean
  data_files: string[]
}

const emit = defineEmits<{
  (e: 'select', templateId: string): void
}>()

const templates = ref<TemplateInfo[]>([])
const loading = ref(false)
const error = ref('')
const searchQuery = ref('')
const selectedCategory = ref<string>('all')

const categories = computed(() => {
  const cats = new Set(templates.value.map(t => t.category))
  return ['all', ...Array.from(cats).sort()]
})

const filteredTemplates = computed(() => {
  let result = templates.value
  
  if (selectedCategory.value !== 'all') {
    result = result.filter(t => t.category === selectedCategory.value)
  }
  
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(t => 
      t.name.toLowerCase().includes(query) ||
      t.category.toLowerCase().includes(query) ||
      t.description.toLowerCase().includes(query)
    )
  }
  
  return result
})

async function fetchTemplates() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/templates')
    templates.value = data
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? String(e)
  } finally {
    loading.value = false
  }
}

function getThumbnailUrl(template: TemplateInfo): string {
  // 如果有缩略图路径，使用图片API
  if (template.thumbnail) {
    // 对路径的每个部分分别编码，保留 / 分隔符
    const encodedPath = template.thumbnail.split('/').map(p => encodeURIComponent(p)).join('/')
    return `/api/templates/image/${encodedPath}`
  }
  // 否则尝试使用默认的thumbnail端点
  const encodedId = template.id.split('/').map(p => encodeURIComponent(p)).join('/')
  return `/api/templates/${encodedId}/thumbnail`
}

function handleThumbnailError(e: Event) {
  const img = e.target as HTMLImageElement
  img.style.display = 'none'
  // 显示占位符
  const placeholder = img.parentElement?.querySelector('.placeholder-thumb') as HTMLElement
  if (placeholder) {
    placeholder.style.display = 'flex'
  }
}

function getCategoryColor(category: string): string {
  // 根据后端按代码推断的图表类型进行配色
  const colors: Record<string, string> = {
    '泰勒图': '#0ea5e9',
    '色标散点图': '#22c55e',
    '散点对比图': '#84cc16',
    '散点图': '#65a30d',
    '热力图': '#ef4444',
    '柱状图': '#f59e0b',
    '折线图': '#6366f1',
    '多曲线': '#8b5cf6',
    '直方图': '#a855f7',
    '箱线图': '#fb7185',
    '小提琴图': '#f472b6',
    '其他': '#6b7280',
    // 兼容旧中文分类名称
    '散点对比图（含色标）': '#22c55e',
    '散点图（含色标）': '#10b981',
    '相关性散点矩阵': '#06b6d4',
    '堆叠柱状图': '#d97706',
    '曲线对比图': '#8b5cf6'
  }
  return colors[category] || '#6b7280'
}

onMounted(fetchTemplates)
</script>

<template>
  <div class="templates-gallery">
    <!-- 顶部搜索和筛选 -->
    <div class="gallery-header">
      <h2>📊 图表模板库</h2>
      <div class="filters">
        <input 
          v-model="searchQuery" 
          class="search-input" 
          placeholder="搜索模板..." 
        />
        <select v-model="selectedCategory" class="category-select">
          <option value="all">全部分类</option>
          <option v-for="cat in categories.slice(1)" :key="cat" :value="cat">
            {{ cat }}
          </option>
        </select>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>加载模板中...</span>
    </div>

    <!-- 错误提示 -->
    <div v-else-if="error" class="error-box">
      {{ error }}
      <button @click="fetchTemplates" class="retry-btn">重试</button>
    </div>

    <!-- 空状态 -->
    <div v-else-if="filteredTemplates.length === 0" class="empty">
      <div class="empty-icon">📭</div>
      <p>没有找到匹配的模板</p>
    </div>

    <!-- 模板网格 -->
    <div v-else class="templates-grid">
      <div 
        v-for="template in filteredTemplates" 
        :key="template.id"
        class="template-card"
        @click="emit('select', template.id)"
      >
        <!-- 缩略图 -->
        <div class="card-thumbnail">
          <img 
            :src="getThumbnailUrl(template)" 
            :alt="template.name"
            @load="(e) => { (e.target as HTMLImageElement).style.opacity = '1'; const ph = (e.target as HTMLElement).parentElement?.querySelector('.placeholder-thumb') as HTMLElement; if(ph) ph.style.display = 'none'; }"
            @error="handleThumbnailError"
            style="opacity: 0; transition: opacity 0.3s;"
          />
          <div class="placeholder-thumb">
            <span class="chart-icon">📊</span>
          </div>
          <!-- 分类标签 -->
          <span 
            class="category-badge" 
            :style="{ backgroundColor: getCategoryColor(template.category) }"
          >
            {{ template.category }}
          </span>
        </div>
        
        <!-- 卡片信息 -->
        <div class="card-info">
          <h3 class="card-title" :title="template.name">{{ template.name }}</h3>
          <p class="card-desc">{{ template.description }}</p>
          <div class="card-meta">
            <span v-if="template.has_data_file" class="data-badge">
              📁 含数据文件
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="gallery-footer">
      共 {{ filteredTemplates.length }} 个模板
      <span v-if="selectedCategory !== 'all'">（{{ selectedCategory }}）</span>
    </div>
  </div>
</template>

<style scoped>
.templates-gallery {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  color: #1e293b;
  overflow: hidden;
}

.gallery-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  background: white;
  flex-shrink: 0;
}

.gallery-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
}

.filters {
  display: flex;
  gap: 10px;
}

.search-input {
  padding: 8px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  color: #1e293b;
  font-size: 14px;
  width: 200px;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.category-select {
  padding: 8px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: white;
  color: #1e293b;
  font-size: 14px;
  cursor: pointer;
}

.loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #64748b;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-box {
  margin: 20px;
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #dc2626;
}

.retry-btn {
  padding: 6px 12px;
  background: #dc2626;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
}

.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #64748b;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.templates-grid {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-content: flex-start;
  background: #f9fafb;
}

.template-card {
  width: calc(33.333% - 11px);
  background: white;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.template-card:hover {
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.card-thumbnail {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 56.25%;
  background: #f3f4f6;
  overflow: hidden;
}

.card-thumbnail img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: white;
}

.placeholder-thumb {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
}

.chart-icon {
  font-size: 72px;
  opacity: 0.3;
}

.category-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  z-index: 10;
}

.card-info {
  padding: 12px 14px;
}

.card-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-desc {
  margin: 0 0 6px 0;
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  gap: 8px;
}

.data-badge {
  font-size: 12px;
  color: #059669;
}

.gallery-footer {
  padding: 12px 24px;
  border-top: 1px solid #e5e7eb;
  font-size: 14px;
  color: #6b7280;
  text-align: center;
  background: white;
  flex-shrink: 0;
}
</style>
