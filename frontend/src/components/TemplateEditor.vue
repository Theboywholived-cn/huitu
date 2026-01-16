<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue'
import api from '../api'
import * as monaco from 'monaco-editor'

interface DataFile {
  name: string
  content: string
  path: string
}

interface TemplateDetail {
  id: string
  name: string
  category: string
  code: string
  data_files: DataFile[]
  description: string
}

const props = defineProps<{
  templateId: string | null
}>()

const emit = defineEmits<{
  (e: 'back'): void
}>()

const template = ref<TemplateDetail | null>(null)
const loading = ref(false)
const error = ref('')

const code = ref('')
const dataFiles = ref<Record<string, string>>({})
const activeDataTab = ref<string>('')

const running = ref(false)
const runError = ref('')
const resultImage = ref<string>('')
const resultImageId = ref<string>('')

// 参数配置弹窗
const showConfigModal = ref(false)
const uploadedFiles = ref<Record<string, File | null>>({})
const useUploadedFile = ref<Record<string, boolean>>({})

const editorContainer = ref<HTMLDivElement | null>(null)
let editor: monaco.editor.IStandaloneCodeEditor | null = null

async function fetchTemplate() {
  if (!props.templateId) return
  
  loading.value = true
  error.value = ''
  
  try {
    const { data } = await api.get(`/templates/${encodeURIComponent(props.templateId)}`)
    template.value = data
    code.value = data.code
    
    // 初始化数据文件
    dataFiles.value = {}
    uploadedFiles.value = {}
    useUploadedFile.value = {}
    if (data.data_files.length > 0) {
      activeDataTab.value = data.data_files[0].name
      for (const df of data.data_files) {
        dataFiles.value[df.name] = df.content
        uploadedFiles.value[df.name] = null
        useUploadedFile.value[df.name] = false
      }
    }
    
    // 初始化编辑器
    setTimeout(initEditor, 100)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? String(e)
  } finally {
    loading.value = false
  }
}

function initEditor() {
  if (!editorContainer.value) return
  
  if (editor) {
    editor.dispose()
  }
  
  editor = monaco.editor.create(editorContainer.value, {
    value: code.value,
    language: 'python',
    theme: 'vs',
    fontSize: 13,
    minimap: { enabled: false },
    automaticLayout: true,
    lineNumbers: 'on',
    scrollBeyondLastLine: false,
    wordWrap: 'on'
  })
  
  editor.onDidChangeModelContent(() => {
    code.value = editor?.getValue() ?? ''
  })
}

// 打开参数配置弹窗
function openConfigModal() {
  showConfigModal.value = true
}

// 处理文件上传
function handleFileUpload(event: Event, fileName: string) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    uploadedFiles.value[fileName] = input.files[0]
    useUploadedFile.value[fileName] = true
    
    // 如果是文本文件，读取内容
    const file = input.files[0]
    if (file.name.endsWith('.csv')) {
      const reader = new FileReader()
      reader.onload = (e) => {
        if (e.target?.result) {
          dataFiles.value[fileName] = e.target.result as string
        }
      }
      reader.readAsText(file)
    }
  }
}

// 确认运行
async function confirmRun() {
  showConfigModal.value = false
  await runCode()
}

async function runCode() {
  running.value = true
  runError.value = ''
  resultImage.value = ''
  
  try {
    // 准备上传的数据
    const formData = new FormData()
    formData.append('code', code.value)
    if (props.templateId) {
      formData.append('template_id', props.templateId)
    }
    
    // 检查是否有上传的二进制文件
    let hasUploadedBinary = false
    for (const [name, file] of Object.entries(uploadedFiles.value)) {
      if (file && useUploadedFile.value[name] && (name.endsWith('.xlsx') || name.endsWith('.xls'))) {
        hasUploadedBinary = true
        formData.append(`file_${name}`, file)
      }
    }
    
    // 如果没有上传二进制文件，使用普通JSON请求
    if (!hasUploadedBinary) {
      const { data } = await api.post('/templates/run', {
        code: code.value,
        template_id: props.templateId,
        data_files: dataFiles.value
      })
      
      if (data.success) {
        resultImage.value = `data:image/png;base64,${data.image_base64}`
        resultImageId.value = data.image_id
      } else {
        runError.value = data.error || '执行失败'
      }
    } else {
      // 有二进制文件，使用FormData上传
      formData.append('data_files_json', JSON.stringify(dataFiles.value))
      
      const { data } = await api.post('/templates/run-with-files', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      if (data.success) {
        resultImage.value = `data:image/png;base64,${data.image_base64}`
        resultImageId.value = data.image_id
      } else {
        runError.value = data.error || '执行失败'
      }
    }
  } catch (e: any) {
    runError.value = e?.response?.data?.detail ?? String(e)
  } finally {
    running.value = false
  }
}

function downloadImage() {
  if (!resultImage.value) return
  
  const a = document.createElement('a')
  a.href = resultImage.value
  a.download = `${template.value?.name || 'chart'}.png`
  a.click()
}

function downloadCode() {
  const blob = new Blob([code.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${template.value?.name || 'script'}.py`
  a.click()
  URL.revokeObjectURL(url)
}

onBeforeUnmount(() => {
  if (editor) {
    editor.dispose()
    editor = null
  }
})

watch(() => props.templateId, fetchTemplate, { immediate: true })
</script>

<template>
  <div class="template-editor">
    <!-- 顶部栏 -->
    <div class="editor-header">
      <button class="back-btn" @click="emit('back')">
        ← 返回模板库
      </button>
      <div class="template-title">
        <span class="category-tag">{{ template?.category }}</span>
        <h2>{{ template?.name || '加载中...' }}</h2>
      </div>
      <div class="header-actions">
        <button class="btn secondary" @click="downloadCode" :disabled="!code">
          📥 下载代码
        </button>
        <button class="btn primary" @click="openConfigModal" :disabled="running || !code">
          {{ running ? '⏳ 执行中...' : '▶️ 运行代码' }}
        </button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="editor-main">
      <!-- 左侧：代码编辑器 -->
      <div class="code-section">
        <div class="section-header">
          <span>Python 代码</span>
          <span class="hint">修改后点击"运行代码"生成图片</span>
        </div>
        <div ref="editorContainer" class="code-editor"></div>
        
        <!-- 数据文件标签页 -->
        <div v-if="template?.data_files.length" class="data-section">
          <div class="data-tabs">
            <button 
              v-for="df in template.data_files" 
              :key="df.name"
              :class="['data-tab', { active: activeDataTab === df.name }]"
              @click="activeDataTab = df.name"
            >
              📄 {{ df.name }}
            </button>
          </div>
          <div class="data-info">
            [Excel文件，请下载后查看]
          </div>
        </div>
      </div>

      <!-- 右侧：结果预览 -->
      <div class="result-section">
        <div class="section-header">
          <span>生成结果</span>
          <button 
            v-if="resultImage" 
            class="btn small secondary" 
            @click="downloadImage"
          >
            💾 下载图片
          </button>
        </div>
        
        <div class="result-content">
          <!-- 加载中 -->
          <div v-if="running" class="result-loading">
            <div class="spinner"></div>
            <p>正在执行代码...</p>
          </div>
          
          <!-- 错误 -->
          <div v-else-if="runError" class="result-error">
            <div class="error-title">❌ 执行出错</div>
            <pre class="error-detail">{{ runError }}</pre>
          </div>
          
          <!-- 结果图片 -->
          <div v-else-if="resultImage" class="result-image">
            <img :src="resultImage" alt="Generated Chart" />
          </div>
          
          <!-- 空状态 -->
          <div v-else class="result-empty">
            <div class="empty-icon">🖼️</div>
            <p>点击"运行代码"生成图表</p>
            <p class="hint">修改代码或数据后重新运行即可更新</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 参数配置弹窗 -->
    <div v-if="showConfigModal" class="modal-overlay" @click.self="showConfigModal = false">
      <div class="config-modal">
        <div class="modal-header">
          <h3>⚙️ 运行配置</h3>
          <button class="close-btn" @click="showConfigModal = false">×</button>
        </div>
        
        <div class="modal-body">
          <!-- 数据文件配置 -->
          <div v-if="template?.data_files.length" class="config-section">
            <h4>📊 数据文件</h4>
            <p class="section-desc">您可以使用模板自带的数据，或上传自己的数据文件</p>
            
            <div class="file-list">
              <div v-for="df in template.data_files" :key="df.name" class="file-item">
                <div class="file-info">
                  <span class="file-icon">{{ df.name.endsWith('.xlsx') ? '📗' : '📄' }}</span>
                  <span class="file-name">{{ df.name }}</span>
                </div>
                
                <div class="file-options">
                  <label class="radio-option">
                    <input 
                      type="radio" 
                      :name="`file_${df.name}`" 
                      :checked="!useUploadedFile[df.name]"
                      @change="useUploadedFile[df.name] = false"
                    />
                    <span>使用模板数据</span>
                  </label>
                  
                  <label class="radio-option">
                    <input 
                      type="radio" 
                      :name="`file_${df.name}`" 
                      :checked="useUploadedFile[df.name]"
                      @change="useUploadedFile[df.name] = true"
                    />
                    <span>上传自定义数据</span>
                  </label>
                </div>
                
                <div v-if="useUploadedFile[df.name]" class="upload-area">
                  <input 
                    type="file" 
                    :accept="df.name.endsWith('.xlsx') ? '.xlsx,.xls' : '.csv'"
                    @change="(e) => handleFileUpload(e, df.name)"
                  />
                  <div v-if="uploadedFiles[df.name]" class="uploaded-info">
                    ✅ 已选择: {{ uploadedFiles[df.name]?.name }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 无数据文件时的提示 -->
          <div v-else class="config-section">
            <h4>📝 运行说明</h4>
            <p class="section-desc">此模板不需要外部数据文件，点击"确认运行"直接执行代码。</p>
          </div>
          
          <!-- 代码参数提示 -->
          <div class="config-section">
            <h4>💡 提示</h4>
            <ul class="tips-list">
              <li>您可以在左侧代码编辑器中修改参数（如颜色、标题等）</li>
              <li>修改数据文件内容可以更改图表数据</li>
              <li>如果遇到报错，请检查数据格式是否正确</li>
            </ul>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn secondary" @click="showConfigModal = false">取消</button>
          <button class="btn primary" @click="confirmRun" :disabled="running">
            {{ running ? '执行中...' : '确认运行' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.template-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  color: #1f2937;
}

.editor-header {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #e5e7eb;
  gap: 16px;
  background: #f9fafb;
}

.back-btn {
  padding: 8px 14px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  color: #4b5563;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.template-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.template-title h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.category-tag {
  padding: 4px 10px;
  background: #3b82f6;
  color: white;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn.primary {
  background: #3b82f6;
  color: white;
}

.btn.primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn.secondary {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  color: #374151;
}

.btn.secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn.small {
  padding: 6px 12px;
  font-size: 13px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.editor-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.code-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e5e7eb;
  min-width: 0;
}

.result-section {
  width: 45%;
  display: flex;
  flex-direction: column;
  min-width: 400px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background: #f3f4f6;
  border-bottom: 1px solid #e5e7eb;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.section-header .hint {
  font-size: 12px;
  color: #64748b;
  font-weight: normal;
}

.code-editor {
  flex: 1;
  min-height: 300px;
}

.data-section {
  border-top: 1px solid #e5e7eb;
  max-height: 200px;
  display: flex;
  flex-direction: column;
}

.data-tabs {
  display: flex;
  gap: 2px;
  background: #f3f4f6;
  padding: 8px 12px 0;
}

.data-tab {
  padding: 8px 14px;
  background: #e5e7eb;
  border: none;
  border-radius: 6px 6px 0 0;
  color: #6b7280;
  cursor: pointer;
  font-size: 13px;
}

.data-tab.active {
  background: white;
  color: #1f2937;
}

.data-info {
  padding: 16px;
  background: #f8fafc;
  color: #64748b;
  font-size: 13px;
  text-align: center;
}

.result-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  overflow: auto;
  background: #f9fafb;
}

.result-loading {
  text-align: center;
  color: #6b7280;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.result-error {
  width: 100%;
  max-height: 100%;
  overflow: auto;
}

.error-title {
  font-size: 16px;
  font-weight: 600;
  color: #ef4444;
  margin-bottom: 12px;
}

.error-detail {
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  font-size: 12px;
  color: #b91c1c;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow: auto;
}

.result-image {
  max-width: 100%;
  max-height: 100%;
}

.result-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.result-empty {
  text-align: center;
  color: #9ca3af;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.result-empty p {
  margin: 8px 0;
}

.result-empty .hint {
  font-size: 13px;
  color: #475569;
}

/* 弹窗样式 */
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

.config-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #1f2937;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 20px;
  cursor: pointer;
  color: #6b7280;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.config-section {
  margin-bottom: 24px;
}

.config-section:last-child {
  margin-bottom: 0;
}

.config-section h4 {
  margin: 0 0 8px 0;
  font-size: 15px;
  color: #1f2937;
}

.section-desc {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: #6b7280;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.file-item {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.file-icon {
  font-size: 20px;
}

.file-name {
  font-weight: 500;
  color: #1f2937;
}

.file-options {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #4b5563;
}

.radio-option input {
  cursor: pointer;
}

.upload-area {
  padding: 12px;
  background: white;
  border: 2px dashed #d1d5db;
  border-radius: 6px;
}

.upload-area input[type="file"] {
  width: 100%;
}

.uploaded-info {
  margin-top: 8px;
  font-size: 13px;
  color: #059669;
}

.tips-list {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.8;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
}
</style>
