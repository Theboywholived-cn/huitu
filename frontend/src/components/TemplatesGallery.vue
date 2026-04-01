<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { fetchTemplates, runTemplate, type TemplateMeta } from '../api'



// ==================== Emits ====================
const emit = defineEmits<{
  select: [template: TemplateMeta]
}>()

// ==================== State ====================
const templates = ref<TemplateMeta[]>([])
const loading = ref(false)
const error = ref('')
const searchQuery = ref('')
const selectedCategory = ref<string>('all')

// Runner Modal state
const showRunnerModal = ref(false)
const selectedTemplate = ref<TemplateMeta | null>(null)
const uploadedFile = ref<File | null>(null)
const isRunning = ref(false)
const runError = ref('')
const resultImageUrl = ref<string | null>(null)

// ==================== Computed ====================
const categories = computed(() => {
  const cats = new Set(templates.value.map(t => t.category))
  return ['all', ...Array.from(cats).sort()]
})

const templatesByCategory = computed(() => {
  const map: Record<string, TemplateMeta[]> = {}
  
  let filtered = templates.value
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(t =>
      t.name.toLowerCase().includes(query) ||
      t.category.toLowerCase().includes(query) ||
      t.tags.some(tag => tag.toLowerCase().includes(query))
    )
  }
  
  if (selectedCategory.value !== 'all') {
    filtered = filtered.filter(t => t.category === selectedCategory.value)
  }
  
  for (const t of filtered) {
    if (!map[t.category]) map[t.category] = []
    map[t.category].push(t)
  }
  
  return map
})

const totalFiltered = computed(() => {
  return Object.values(templatesByCategory.value).reduce((s, arr) => s + arr.length, 0)
})

const canRun = computed(() => !!uploadedFile.value && !isRunning.value)

// ==================== Methods ====================
async function loadTemplates() {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchTemplates()
    templates.value = res.templates
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? String(e)
  } finally {
    loading.value = false
  }
}

function getThumbnailUrl(template: TemplateMeta): string {
  if (template.thumbnail) {
    const encodedPath = template.thumbnail.split('/').map(p => encodeURIComponent(p)).join('/')
    return `/api/templates/image/${encodedPath}`
  }
  return ''
}

function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    '泰勒图': '#0ea5e9',
    '散点图': '#10b981',
    '热力图': '#ef4444',
    '柱状图': '#f59e0b',
    '折线图': '#6366f1',
    '曲面图': '#8b5cf6',
    '箱线图': '#ec4899',
    '小提琴图': '#f472b6',
    '三元图': '#14b8a6',
    '气泡图': '#06b6d4',
    '其他': '#64748b'
  }
  return colors[category] || '#64748b'
}

function openRunner(template: TemplateMeta) {
  selectedTemplate.value = template
  uploadedFile.value = null
  runError.value = ''
  if (resultImageUrl.value) {
    URL.revokeObjectURL(resultImageUrl.value)
    resultImageUrl.value = null
  }
  showRunnerModal.value = true
}

function closeRunner() {
  showRunnerModal.value = false
  selectedTemplate.value = null
  uploadedFile.value = null
  runError.value = ''
  if (resultImageUrl.value) {
    URL.revokeObjectURL(resultImageUrl.value)
    resultImageUrl.value = null
  }
}

function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    uploadedFile.value = input.files[0]
  }
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    const file = e.dataTransfer.files[0]
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (['csv', 'xlsx', 'xls'].includes(ext || '')) {
      uploadedFile.value = file
    } else {
      runError.value = '仅支持 .csv, .xlsx, .xls 格式'
    }
  }
}

function handleDragOver(e: DragEvent) {
  e.preventDefault()
}

async function executeRun() {
  if (!selectedTemplate.value || !uploadedFile.value) return
  
  isRunning.value = true
  runError.value = ''
  if (resultImageUrl.value) {
    URL.revokeObjectURL(resultImageUrl.value)
    resultImageUrl.value = null
  }
  
  try {
    const blob = await runTemplate(selectedTemplate.value.id, uploadedFile.value)
    resultImageUrl.value = URL.createObjectURL(blob)
  } catch (e: any) {
    // Handle blob error response
    if (e?.response?.data instanceof Blob) {
      try {
        const text = await e.response.data.text()
        const parsed = JSON.parse(text)
        runError.value = parsed.detail || '执行失败'
      } catch {
        runError.value = '执行失败，无法解析错误信息'
      }
    } else {
      runError.value = e?.response?.data?.detail || e?.message || String(e)
    }
  } finally {
    isRunning.value = false
  }
}

function downloadImage() {
  if (!resultImageUrl.value || !selectedTemplate.value) return
  const a = document.createElement('a')
  a.href = resultImageUrl.value
  a.download = `${selectedTemplate.value.name}_output.png`
  a.click()
}

onMounted(loadTemplates)
</script>

<template>
  <div class="templates-gallery">
    <!-- Header -->
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

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>加载模板中...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-box">
      {{ error }}
      <button @click="loadTemplates" class="retry-btn">重试</button>
    </div>

    <!-- Empty -->
    <div v-else-if="totalFiltered === 0" class="empty">
      <div class="empty-icon">📭</div>
      <p>没有找到匹配的模板</p>
    </div>

    <!-- Categorized Grid -->
    <div v-else class="categories-container">
      <div 
        v-for="(tpls, cat) in templatesByCategory" 
        :key="cat" 
        class="category-section"
      >
        <h3 class="category-heading">
          <span 
            class="category-dot" 
            :style="{ backgroundColor: getCategoryColor(cat) }"
          ></span>
          {{ cat }}
          <span class="category-count">{{ tpls.length }}</span>
        </h3>
        <div class="templates-grid">
          <div 
            v-for="template in tpls" 
            :key="template.id"
            class="template-card"
            @click="emit('select', template)"
          >
            <div class="card-thumbnail">
              <img 
                v-if="template.thumbnail"
                :src="getThumbnailUrl(template)" 
                :alt="template.name"
                class="thumb-img"
                @load="(e) => { (e.target as HTMLImageElement).classList.add('loaded'); (e.target as HTMLElement).parentElement?.classList.add('has-image'); }"
                @error="(e) => { (e.target as HTMLImageElement).style.display = 'none' }"
              />
              <div class="placeholder-thumb">
                <span class="chart-icon">📊</span>
              </div>
              <span 
                class="category-badge" 
                :style="{ backgroundColor: getCategoryColor(template.category) }"
              >
                {{ template.category }}
              </span>
            </div>
            <div class="card-info">
              <h3 class="card-title" :title="template.name">{{ template.name }}</h3>
              <div class="card-tags" v-if="template.tags.length">
                <span v-for="tag in template.tags.slice(0, 2)" :key="tag" class="tag">{{ tag }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="gallery-footer">
      共 {{ totalFiltered }} 个模板
      <span v-if="selectedCategory !== 'all'">（{{ selectedCategory }}）</span>
    </div>

    <!-- ==================== Runner Modal ==================== -->
    <div v-if="showRunnerModal" class="modal-overlay" @click.self="closeRunner">
      <div class="modal-content">
        <!-- Modal Header -->
        <div class="modal-header">
          <h3>🚀 运行模板</h3>
          <button class="close-btn" @click="closeRunner">✕</button>
        </div>
        
        <!-- Modal Body -->
        <div class="modal-body">
          <!-- Template Info -->
          <div class="template-info-row">
            <span class="info-label">模板名称：</span>
            <span class="info-value">{{ selectedTemplate?.name }}</span>
          </div>
          <div class="template-info-row">
            <span class="info-label">分类：</span>
            <span 
              class="info-badge" 
              :style="{ backgroundColor: getCategoryColor(selectedTemplate?.category || '') }"
            >
              {{ selectedTemplate?.category }}
            </span>
          </div>

          <!-- File Upload Area -->
          <div 
            class="upload-zone"
            :class="{ 'has-file': uploadedFile }"
            @drop="handleDrop"
            @dragover="handleDragOver"
          >
            <template v-if="!uploadedFile">
              <div class="upload-icon">📁</div>
              <p class="upload-text">拖拽文件到此处，或点击选择</p>
              <p class="upload-hint">支持 .csv, .xlsx, .xls 格式</p>
              <input 
                type="file" 
                accept=".csv,.xlsx,.xls"
                class="file-input"
                @change="handleFileChange"
              />
            </template>
            <template v-else>
              <div class="file-selected">
                <span class="file-icon">📄</span>
                <span class="file-name">{{ uploadedFile.name }}</span>
                <button class="remove-file" @click.stop="uploadedFile = null">✕</button>
              </div>
            </template>
          </div>

          <!-- Run Button -->
          <button 
            class="run-btn"
            :disabled="!canRun"
            @click="executeRun"
          >
            <template v-if="isRunning">
              <span class="btn-spinner"></span>
              正在运行...
            </template>
            <template v-else>
              ▶ 运行分析
            </template>
          </button>

          <!-- Error Display -->
          <div v-if="runError" class="run-error">
            <strong>错误：</strong>
            <pre>{{ runError }}</pre>
          </div>

          <!-- Result Image -->
          <div v-if="resultImageUrl" class="result-section">
            <div class="result-header">
              <span>✅ 生成成功</span>
              <button class="download-btn" @click="downloadImage">
                ⬇ 下载图片
              </button>
            </div>
            <div class="result-image-container">
              <img :src="resultImageUrl" alt="生成的图表" />
            </div>
          </div>
        </div>
      </div>
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
  padding: 20px 32px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  flex-shrink: 0;
}

.gallery-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
}

.filters {
  display: flex;
  gap: 12px;
}

.search-input {
  padding: 10px 16px;
  padding-left: 38px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: white;
  color: #1e293b;
  font-size: 14px;
  width: 240px;
  transition: all 0.2s ease;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%239ca3af'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: 12px center;
  background-size: 18px;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.search-input::placeholder {
  color: #9ca3af;
}

.category-select {
  padding: 10px 16px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: white;
  color: #1e293b;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 130px;
}

.category-select:hover {
  border-color: #3b82f6;
}

.category-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
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

/* ==================== Categorized Layout ==================== */
.categories-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.category-section {
  margin-bottom: 36px;
}

.category-section:last-child {
  margin-bottom: 16px;
}

.category-heading {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 18px 0;
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

.category-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.category-count {
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
  background: #e5e7eb;
  padding: 2px 10px;
  border-radius: 12px;
  margin-left: auto;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.template-card {
  background: white;
  border-radius: 14px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  border: 1px solid #f1f5f9;
}

.template-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12), 0 4px 8px rgba(0, 0, 0, 0.08);
  border-color: #e2e8f0;
}

.card-thumbnail {
  position: relative;
  width: 100%;
  height: 0;
  padding-bottom: 65%;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
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
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 2;
}

.card-thumbnail img.loaded {
  opacity: 1;
}

.card-thumbnail.has-image .placeholder-thumb {
  display: none;
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
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  z-index: 1;
}

.chart-icon {
  font-size: 56px;
  opacity: 0.3;
  filter: grayscale(30%);
}

.category-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  color: white;
  z-index: 3;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(4px);
  letter-spacing: 0.3px;
}

.card-info {
  padding: 14px 16px;
  background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
}

.card-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.card-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  font-size: 11px;
  padding: 2px 8px;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 4px;
}

.gallery-footer {
  padding: 14px 32px;
  border-top: 1px solid #e5e7eb;
  font-size: 13px;
  color: #64748b;
  text-align: center;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  flex-shrink: 0;
  font-weight: 500;
  letter-spacing: 0.3px;
}

/* ==================== Modal ==================== */
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
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #e5e7eb;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-btn:hover {
  background: #d1d5db;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.template-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 14px;
}

.info-label {
  color: #6b7280;
}

.info-value {
  font-weight: 600;
  color: #111827;
}

.info-badge {
  padding: 3px 10px;
  border-radius: 4px;
  font-size: 12px;
  color: white;
  font-weight: 500;
}

/* Upload Zone */
.upload-zone {
  margin-top: 16px;
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 32px 20px;
  text-align: center;
  position: relative;
  transition: all 0.2s;
  cursor: pointer;
}

.upload-zone:hover {
  border-color: #3b82f6;
  background: #f0f9ff;
}

.upload-zone.has-file {
  border-style: solid;
  border-color: #22c55e;
  background: #f0fdf4;
}

.upload-icon {
  font-size: 40px;
  margin-bottom: 8px;
}

.upload-text {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.upload-hint {
  margin: 0;
  font-size: 12px;
  color: #9ca3af;
}

.file-input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.file-selected {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.file-icon {
  font-size: 24px;
}

.file-name {
  font-weight: 500;
  color: #059669;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-file {
  width: 24px;
  height: 24px;
  border: none;
  background: #dc2626;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Run Button */
.run-btn {
  width: 100%;
  margin-top: 20px;
  padding: 14px;
  font-size: 15px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.run-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.run-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Error Display */
.run-error {
  margin-top: 16px;
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 13px;
}

.run-error pre {
  margin: 8px 0 0 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: ui-monospace, monospace;
  font-size: 12px;
  max-height: 150px;
  overflow-y: auto;
}

/* Result Section */
.result-section {
  margin-top: 20px;
  border: 1px solid #d1fae5;
  border-radius: 12px;
  overflow: hidden;
  background: #f0fdf4;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #dcfce7;
  font-weight: 500;
  color: #166534;
}

.download-btn {
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  color: white;
  background: #16a34a;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.download-btn:hover {
  background: #15803d;
}

.result-image-container {
  padding: 16px;
  background: white;
  display: flex;
  justify-content: center;
}

.result-image-container img {
  max-width: 100%;
  max-height: 400px;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>

















































