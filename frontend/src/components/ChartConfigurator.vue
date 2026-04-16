<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue'
import api from '../api'

// 图形配置接口
interface ChartConfig {
  // 数据源配置
  dataFile: string | null
  dataColumns: string[]
  selectedColumns: string[]
  
  // 图形数量配置
  chartCount: number
  maxChartCount: number
  gridRows: number
  gridCols: number
  
  // 数据点样式
  markerShape: 'circle' | 'square' | 'triangle' | 'diamond' | 'star' | 'plus' | 'cross'
  markerSize: number
  
  // 文字显示
  showLabels: boolean
  showFormulas: boolean
  showLegend: boolean
  showTitle: boolean
  titleText: string
  
  // Colorbar 设置
  useColorbar: boolean
  colorbarMin: number | null
  colorbarMax: number | null
  colormap: string
}

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

// 模板数据
const template = ref<TemplateDetail | null>(null)
const loading = ref(false)
const error = ref('')

// 图形配置
const config = ref<ChartConfig>({
  dataFile: null,
  dataColumns: [],
  selectedColumns: [],
  chartCount: 0,  // 从数据自动识别
  maxChartCount: 0,
  gridRows: 1,
  gridCols: 1,
  markerShape: 'circle',
  markerSize: 6,
  showLabels: true,
  showFormulas: false,
  showLegend: true,
  showTitle: true,
  titleText: '',
  useColorbar: false,
  colorbarMin: null,
  colorbarMax: null,
  colormap: 'viridis'
})

// 上传的自定义文件（支持多个）
const uploadedFiles = ref<Array<{ file: File; content: string; name: string }>>([])
const parsedData = ref<any[]>([])
const isDataAnalyzed = ref(false) // 标记数据是否已分析
// 自动识别到的配对列（每一组对应 1 幅子图）
const detectedPairs = ref<Array<{ name: string; col0: string; col1: string }>>([])
// 用户选择要生成的图表索引
const selectedPairIndices = ref<number[]>([])

// 运行状态
const running = ref(false)
const runError = ref('')
const runNotice = ref('')
const resultImage = ref<string>('')

// 泰勒图（Taylor Diagram）专用：列映射与参数
const isTaylorTemplate = computed(() => {
  const name = template.value?.name ?? ''
  const category = template.value?.category ?? ''
  const id = template.value?.id ?? ''
  return name.includes('泰勒图') || category.includes('泰勒图') || id.includes('泰勒图')
})

const taylorModelColumn = ref<string>('')
const taylorCorrColumn = ref<string>('')
const taylorStdColumn = ref<string>('')
const taylorRefStd = ref<number>(1.0)

// 形状选项
const shapeOptions = [
  { value: 'circle', label: '圆形 ●', marker: 'o' },
  { value: 'square', label: '方形 ■', marker: 's' },
  { value: 'triangle', label: '三角形 ▲', marker: '^' },
  { value: 'diamond', label: '菱形 ◆', marker: 'D' },
  { value: 'star', label: '星形 ★', marker: '*' },
  { value: 'plus', label: '加号 +', marker: '+' },
  { value: 'cross', label: '叉号 ×', marker: 'x' }
]

// 颜色映射选项
const colormapOptions = [
  { value: 'viridis', label: 'Viridis (默认)' },
  { value: 'plasma', label: 'Plasma' },
  { value: 'inferno', label: 'Inferno' },
  { value: 'magma', label: 'Magma' },
  { value: 'cividis', label: 'Cividis' },
  { value: 'rainbow', label: 'Rainbow' },
  { value: 'jet', label: 'Jet' },
  { value: 'coolwarm', label: 'Coolwarm' },
  { value: 'RdYlBu', label: 'Red-Yellow-Blue' },
  { value: 'Spectral', label: 'Spectral' }
]

// 选中的配对列（用户选择要生成的图表）
const selectedPairs = computed(() => {
  return selectedPairIndices.value
    .filter(i => i >= 0 && i < detectedPairs.value.length)
    .map(i => detectedPairs.value[i])
})

// 实际要生成的图表数量（基于用户选择）
const effectiveChartCount = computed(() => selectedPairs.value.length)

// 网格容量计算
const gridCapacity = computed(() => config.value.gridRows * config.value.gridCols)

// 最大网格尺寸（根据图表数量动态调整）
const maxGridSize = computed(() => {
  const count = effectiveChartCount.value
  if (count <= 4) return 2
  if (count <= 9) return 3
  if (count <= 16) return 4
  return 5
})

// 网格布局选项（保留用于其他地方可能的使用）
const layoutOptions = computed(() => {
  const options = []
  const max = maxGridSize.value
  for (let r = 1; r <= max; r++) {
    for (let c = 1; c <= max; c++) {
      if (r * c >= effectiveChartCount.value) {
        options.push({ rows: r, cols: c, label: `${r}×${c} (${r * c}个)` })
      }
    }
  }
  return options
})

// 加载模板
async function fetchTemplate() {
  if (!props.templateId) return
  
  loading.value = true
  error.value = ''
  
  try {
    const { data } = await api.get(`/templates/${encodeURIComponent(props.templateId)}`)
    template.value = data
    
    // 初始化配置
    if (data.data_files.length > 0) {
      config.value.dataFile = data.data_files[0].name
      parseDataFile(data.data_files[0].content, data.data_files[0].name)
    }
    
    config.value.titleText = data.name
    
    // 尝试从代码中解析图形数量
    analyzeTemplateCode(data.code)
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? String(e)
  } finally {
    loading.value = false
  }
}

// 分析模板代码，提取配置信息
function analyzeTemplateCode(code: string) {
  // 尝试检测 subplot 布局
  const subplotMatch = code.match(/subplots?\s*\(\s*(\d+)\s*,\s*(\d+)/i)
  if (subplotMatch) {
    config.value.gridRows = parseInt(subplotMatch[1])
    config.value.gridCols = parseInt(subplotMatch[2])
    config.value.chartCount = config.value.gridRows * config.value.gridCols
  }
  
  // 检测是否有 colorbar
  if (code.includes('colorbar') || code.includes('cbar')) {
    config.value.useColorbar = true
  }
  
  // 检测 marker 设置
  const markerMatch = code.match(/marker\s*=\s*['"](\w)['"]/)
  if (markerMatch) {
    const markerMap: Record<string, string> = {
      'o': 'circle', 's': 'square', '^': 'triangle',
      'D': 'diamond', '*': 'star', '+': 'plus', 'x': 'cross'
    }
    const shape = markerMap[markerMatch[1]]
    if (shape) config.value.markerShape = shape as any
  }
}

// 解析数据文件并自动识别图表数量
function parseDataFile(content: string, filename: string) {
  console.log('开始解析文件:', filename, '内容长度:', content.length)
  try {
    const isCSV = filename.endsWith('.csv')
    const isExcel = filename.endsWith('.xlsx') || filename.endsWith('.xls')
    
    // CSV 文件或已转换为 CSV 格式的 Excel 文件都可以直接解析
    // Excel 上传时已在后端转换为 CSV 格式
    if (isCSV || isExcel) {
      const lines = content.trim().split('\n')
      console.log('数据行数:', lines.length)
      if (lines.length > 0) {
        // 假设第一行是标题
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
        console.log('识别到的列:', headers)
        config.value.dataColumns = headers
        config.value.selectedColumns = headers.slice(0, Math.min(4, headers.length))
        
        // 解析数据
        parsedData.value = lines.slice(1).map(line => {
          const values = line.split(',')
          const row: Record<string, any> = {}
          headers.forEach((h, i) => {
            row[h] = values[i]?.trim()
          })
          return row
        })
        
        // 自动识别图表数量：根据数据列数或数据分组
        if (isTaylorTemplate.value) {
          // 泰勒图只需要 1 张图，且需要列映射（模型/相关系数/标准差）
          const detected = detectTaylorColumns(headers)
          taylorModelColumn.value = detected.model
          taylorCorrColumn.value = detected.corr
          taylorStdColumn.value = detected.std
          detectedPairs.value = []
          selectedPairIndices.value = []
          config.value.chartCount = 1
          config.value.gridRows = 1
          config.value.gridCols = 1
        } else {
          detectedPairs.value = detectPairedColumns(headers)
          console.log('识别到的配对:', detectedPairs.value)
          autoDetectChartCount(headers, parsedData.value)
        }
      }
    }
  } catch (e) {
    console.error('解析数据文件失败:', e)
  }
}

function detectTaylorColumns(headers: string[]): { model: string; corr: string; std: string } {
  const normalized = headers.map(h => ({ raw: h, k: h.toLowerCase() }))

  const pickFirst = (pred: (k: string) => boolean) => normalized.find(x => pred(x.k))?.raw ?? ''

  const model =
    pickFirst(k => k.includes('model')) ||
    pickFirst(k => k.includes('模型')) ||
    pickFirst(k => k.includes('算法')) ||
    pickFirst(k => k.includes('方法')) ||
    headers[0] || ''

  const corr =
    pickFirst(k => k.includes('corr')) ||
    pickFirst(k => k.includes('correlation')) ||
    pickFirst(k => k.includes('相关')) ||
    pickFirst(k => k.includes('r')) ||
    ''

  const std =
    pickFirst(k => k.includes('std')) ||
    pickFirst(k => k.includes('stdev')) ||
    pickFirst(k => k.includes('standard')) ||
    pickFirst(k => k.includes('标准差')) ||
    ''

  return { model, corr, std }
}

// 自动识别图表数量
function autoDetectChartCount(headers: string[], data: any[]) {
  let detectedCount = 1
  let detectionMethod = ''
  
  // 策略1: 检测 _0/_1 或 _pred/_true 配对列（如 CNN_LSTM_0, CNN_LSTM_1）
  const pairedColumns = detectPairedColumns(headers)
  if (pairedColumns.length > 0) {
    detectedCount = pairedColumns.length
    detectionMethod = `检测到 ${detectedCount} 组配对数据列`
    console.log('配对检测:', pairedColumns)
  }
  // 策略2: 检查是否有 "图1", "图2" 等分组列
  else {
    const chartGroupCol = headers.find(h => 
      /^(图|chart|group|分组|类别|model|模型)/i.test(h)
    )
    if (chartGroupCol) {
      const uniqueGroups = new Set(data.map(row => row[chartGroupCol]))
      detectedCount = uniqueGroups.size
      detectionMethod = `按 "${chartGroupCol}" 列分组`
    }
    // 策略3: 检查是否有多组 Y 值列（如 Y1, Y2, Y3...）
    else {
      const yColumns = headers.filter(h => 
        /^(y\d+|value\d+|值\d+|数据\d+)/i.test(h)
      )
      if (yColumns.length > 1) {
        detectedCount = yColumns.length
        detectionMethod = `检测到 ${yColumns.length} 组Y值列`
      } else {
        // 策略4: 默认使用所有数值列数量
        const numericCols = headers.filter(h => {
          const values = data.slice(0, 10).map(row => row[h])
          const numericCount = values.filter(v => !isNaN(parseFloat(v))).length
          return numericCount > values.length / 2
        })
        if (numericCols.length >= 2) {
          // 假设每2列为一组（X,Y配对）
          detectedCount = Math.max(1, Math.floor(numericCols.length / 2))
          detectionMethod = `${numericCols.length} 个数值列，推测 ${detectedCount} 组`
        }
      }
    }
  }
  
  console.log(`图表数量检测: ${detectedCount} (${detectionMethod || '默认'})`)
  
  // 更新配置
  config.value.chartCount = detectedCount
  config.value.maxChartCount = detectedCount
  
  // 自动计算最优网格布局
  updateGridLayout(detectedCount)
}

// 检测配对列（如 XXX_0/XXX_1, XXX_pred/XXX_true）
function detectPairedColumns(headers: string[]): Array<{name: string, col0: string, col1: string}> {
  const pairs: Array<{name: string, col0: string, col1: string}> = []
  const processed = new Set<string>()
  
  // 匹配模式: XXX_0/XXX_1, XXX_pred/XXX_true, XXX_预测/XXX_实际
  const pairPatterns = [
    { suffix0: /_0$/, suffix1: /_1$/, extract: (s: string) => s.replace(/_[01]$/, '') },
    { suffix0: /_pred$/i, suffix1: /_true$/i, extract: (s: string) => s.replace(/_(pred|true)$/i, '') },
    { suffix0: /_预测$/, suffix1: /_实际$/, extract: (s: string) => s.replace(/_(预测|实际)$/, '') },
    { suffix0: /_predict$/i, suffix1: /_actual$/i, extract: (s: string) => s.replace(/_(predict|actual)$/i, '') },
  ]
  
  for (const header of headers) {
    if (processed.has(header)) continue
    
    for (const pattern of pairPatterns) {
      if (pattern.suffix0.test(header)) {
        const baseName = pattern.extract(header)
        // 查找对应的配对列
        const pairHeader = headers.find(h => 
          h !== header && pattern.suffix1.test(h) && pattern.extract(h) === baseName
        )
        if (pairHeader) {
          pairs.push({ name: baseName, col0: header, col1: pairHeader })
          processed.add(header)
          processed.add(pairHeader)
          break
        }
      } else if (pattern.suffix1.test(header)) {
        const baseName = pattern.extract(header)
        const pairHeader = headers.find(h => 
          h !== header && pattern.suffix0.test(h) && pattern.extract(h) === baseName
        )
        if (pairHeader) {
          pairs.push({ name: baseName, col0: pairHeader, col1: header })
          processed.add(header)
          processed.add(pairHeader)
          break
        }
      }
    }
  }
  
  return pairs
}

// 根据图表数量计算最优网格布局
function updateGridLayout(count: number) {
  if (count <= 1) {
    config.value.gridRows = 1
    config.value.gridCols = 1
  } else if (count <= 2) {
    config.value.gridRows = 1
    config.value.gridCols = 2
  } else if (count <= 4) {
    config.value.gridRows = 2
    config.value.gridCols = 2
  } else if (count <= 6) {
    config.value.gridRows = 2
    config.value.gridCols = 3
  } else if (count <= 9) {
    config.value.gridRows = 3
    config.value.gridCols = 3
  } else if (count <= 12) {
    config.value.gridRows = 3
    config.value.gridCols = 4
  } else {
    config.value.gridRows = 4
    config.value.gridCols = 4
  }
}

// 处理文件上传（支持多个文件）
async function handleFileUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  
  const filesToProcess: File[] = []
  
  // 检查并收集需要处理的文件
  for (let i = 0; i < input.files.length; i++) {
    const file = input.files[i]
    // 检查是否已经上传过这个文件
    if (uploadedFiles.value.some(f => f.name === file.name)) {
      console.log(`文件 ${file.name} 已存在，跳过`)
      continue
    }
    filesToProcess.push(file)
  }
  
  if (filesToProcess.length === 0) {
    input.value = ''
    return
  }
  
  const isFirstBatch = uploadedFiles.value.length === 0
  
  // 处理所有文件
  for (const file of filesToProcess) {
    const filename = file.name.toLowerCase()
    console.log('处理文件:', file.name, '小写文件名:', filename)
    
    if (filename.endsWith('.csv')) {
      // CSV 文件直接读取
      await new Promise<void>((resolve) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          if (e.target?.result) {
            const content = e.target.result as string
            console.log('CSV文件读取完成:', file.name, '长度:', content.length)
            uploadedFiles.value.push({ file, content, name: file.name })
          }
          resolve()
        }
        reader.onerror = () => {
          console.error('读取文件失败:', file.name)
          resolve()
        }
        reader.readAsText(file)
      })
    } else if (filename.endsWith('.xlsx') || filename.endsWith('.xls')) {
      // Excel 文件发送到后端解析（不立即解析数据）
      console.log('处理Excel文件:', file.name)
      await parseExcelFile(file, false)
    }
  }
  
  console.log('所有文件已上传，共', uploadedFiles.value.length, '个文件')
  isDataAnalyzed.value = false
  
  // 清空 input，允许重复选择同一文件
  input.value = ''
}

// 解析 Excel 文件（通过后端）
async function parseExcelFile(file: File, shouldParse: boolean = false) {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const { data } = await api.post('/templates/parse-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    if (data.headers && data.rows) {
      // 转换为 CSV 格式存储
      const csvLines = [data.headers.join(',')]
      for (const row of data.rows) {
        csvLines.push(data.headers.map((h: string) => row[h] ?? '').join(','))
      }
      const content = csvLines.join('\n')
      
      // 添加到上传文件列表
      uploadedFiles.value.push({ file, content, name: file.name })
      
      // 只在需要时解析数据
      if (shouldParse) {
        config.value.dataColumns = data.headers
        config.value.selectedColumns = data.headers.slice(0, Math.min(4, data.headers.length))
        parsedData.value = data.rows
        detectedPairs.value = detectPairedColumns(data.headers)
        autoDetectChartCount(data.headers, data.rows)
      }
    }
  } catch (e: any) {
    console.error('解析 Excel 失败:', e)
    runError.value = 'Excel 解析失败: ' + (e?.response?.data?.detail ?? String(e))
  }
}

// 删除上传的文件
function removeUploadedFile(index: number) {
  uploadedFiles.value.splice(index, 1)
  
  // 如果已经分析过数据，需要重新分析
  if (isDataAnalyzed.value) {
    isDataAnalyzed.value = false
    parsedData.value = []
    detectedPairs.value = []
    selectedPairIndices.value = []
    config.value.dataColumns = []
    config.value.chartCount = 0
  }
}

// 开始分析上传的文件
function analyzeUploadedFiles() {
  if (uploadedFiles.value.length === 0) {
    runError.value = '请先上传文件'
    return
  }
  
  console.log('开始分析文件，共', uploadedFiles.value.length, '个文件')
  runError.value = ''
  const firstFile = uploadedFiles.value[0]
  parseDataFile(firstFile.content, firstFile.name)
  isDataAnalyzed.value = true
  
  // 如果没有检测到配对列，自动从前两列生成默认配对
  if (detectedPairs.value.length === 0 && config.value.dataColumns.length >= 2) {
    console.log('未检测到配对列，自动生成默认配对')
    // 使用第一列和第二列作为默认配对
    detectedPairs.value = [{
      name: `${config.value.dataColumns[0]} vs ${config.value.dataColumns[1]}`,
      col0: config.value.dataColumns[1],
      col1: config.value.dataColumns[0]
    }]
    selectedPairIndices.value = [0]
    // 分析成功，不显示错误信息
    console.log('已自动生成默认配对，可以点击"开始"生成图表')
  } else if (detectedPairs.value.length > 0) {
    // 自动选择所有检测到的配对
    selectedPairIndices.value = detectedPairs.value.map((_, i) => i)
    console.log(`已识别到 ${detectedPairs.value.length} 个图表配对`)
  }
}

// 生成 Python 代码
function generateCode(): string {
  if (isTaylorTemplate.value) {
    return generateTaylorCode()
  }
  const markerMap: Record<string, string> = {
    'circle': 'o', 'square': 's', 'triangle': '^',
    'diamond': 'D', 'star': '*', 'plus': '+', 'cross': 'x'
  }
  const marker = markerMap[config.value.markerShape] || 'o'
  const rows = config.value.gridRows
  const cols = config.value.gridCols
  // 使用用户选择的图表配对
  const pairs = selectedPairs.value
  const pairsJson = JSON.stringify(pairs)
  // 计算实际会发送给后端的文件名（需要与 runCode 函数中的逻辑一致）
  let dataFileName = 'data.csv'
  if (uploadedFiles.value.length > 0) {
    const origName = uploadedFiles.value[0].name
    if (origName.toLowerCase().endsWith('.csv')) {
      dataFileName = origName
    } else {
      // 与 runCode 中的转换逻辑保持一致
      dataFileName = origName.replace(/\.(xlsx|xls)$/i, '.csv')
    }
  } else if (config.value.dataFile) {
    dataFileName = config.value.dataFile
  }
  const showFormulas = config.value.showFormulas ? 'True' : 'False'
  // 转义标题文本中的特殊字符（单引号、反斜杠、换行符）
  const safeTitleText = (config.value.titleText || '')
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '')
  const code = `# 自动生成的绘图代码
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

try:
    from scipy.stats import gaussian_kde
except:
    gaussian_kde = None

def _r2_score(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - ss_res / ss_tot if ss_tot != 0 else float('nan')

def _rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))

PAIRS = ${pairsJson}
DATA_FILE = r"${dataFileName}"
MARKER = '${marker}'
MARKER_SIZE = ${config.value.markerSize}
SHOW_LABELS = ${config.value.showLabels ? 'True' : 'False'}
SHOW_TITLE = ${config.value.showTitle ? 'True' : 'False'}
TITLE_TEXT = '${safeTitleText}'
USE_COLORBAR = ${config.value.useColorbar ? 'True' : 'False'}
COLORBAR_MIN = ${config.value.colorbarMin ?? 'None'}
COLORBAR_MAX = ${config.value.colorbarMax ?? 'None'}
COLORMAP = '${config.value.colormap}'
SHOW_FORMULAS = ${showFormulas}

fig, axes = plt.subplots(${rows}, ${cols}, figsize=(${cols * 4.5}, ${rows * 4}))
if ${rows * cols} == 1:
    axes = np.array([axes])
axes = axes.flatten()

def _read_table(path):
    import os
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.xlsx', '.xls']:
        return pd.read_excel(path)
    return pd.read_csv(path)

df = _read_table(DATA_FILE)
if not PAIRS:
    raise RuntimeError('未检测到配对列')

n_charts = len(PAIRS)
sc_for_cbar = None

for i, p in enumerate(PAIRS):
    ax = axes[i]
    col_pred, col_true = p['col0'], p['col1']
    name = p.get('name', f'图{i+1}')
    x = pd.to_numeric(df[col_true], errors='coerce').to_numpy()
    y = pd.to_numeric(df[col_pred], errors='coerce').to_numpy()
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    z = None
    if gaussian_kde and len(x) >= 5:
        try:
            xy = np.vstack([x, y])
            z = gaussian_kde(xy)(xy)
            idx = np.argsort(z)
            x, y, z = x[idx], y[idx], z[idx]
        except:
            pass
    if z is not None:
        sc = ax.scatter(x, y, c=z, cmap=COLORMAP, marker=MARKER, s=MARKER_SIZE**2, vmin=COLORBAR_MIN, vmax=COLORBAR_MAX)
        sc_for_cbar = sc
    else:
        ax.scatter(x, y, color='#1f77b4', marker=MARKER, s=MARKER_SIZE**2)
    if len(x) > 0:
        vmin, vmax = float(min(x.min(), y.min())), float(max(x.max(), y.max()))
        pad = (vmax - vmin) * 0.05 or 1.0
        ax.plot([vmin-pad, vmax+pad], [vmin-pad, vmax+pad], 'k-', lw=1)
        ax.set_xlim(vmin-pad, vmax+pad)
        ax.set_ylim(vmin-pad, vmax+pad)
    if len(x) >= 2:
        k, b = np.polyfit(x, y, 1)
        xs = np.array([x.min(), x.max()])
        ax.plot(xs, k*xs+b, 'r-', lw=1)
        r2, rmse = _r2_score(x, y), _rmse(x, y)
        if SHOW_FORMULAS:
            ax.text(0.05, 0.88, f'y = {k:.3f}x + {b:.3f}', transform=ax.transAxes, fontsize=9)
            ax.text(0.05, 0.78, f'R² = {r2:.2f}', transform=ax.transAxes, fontsize=9)
            ax.text(0.05, 0.68, f'RMSE = {rmse:.2f}', transform=ax.transAxes, fontsize=9)
    if SHOW_TITLE:
        t = str(name)
        for pf in ['PHIT', 'PHI', 'phi']:
            if t.startswith(pf): t = t[len(pf):]
        ax.set_title(t.lstrip('_') or name, fontweight='bold')
    if SHOW_LABELS:
        ax.set_xlabel('实测值')
        ax.set_ylabel('预测值')

for i in range(n_charts, len(axes)):
    axes[i].set_visible(False)

if SHOW_TITLE and TITLE_TEXT:
    fig.suptitle(TITLE_TEXT, fontsize=14, fontweight='bold')

if USE_COLORBAR and sc_for_cbar is not None:
    fig.colorbar(sc_for_cbar, ax=axes[:n_charts], fraction=0.03, pad=0.02, label='Density')

plt.tight_layout()
plt.savefig('output.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
`
  return code
}

function generateTaylorCode(): string {
  // 文件名需与 runCode 中写入临时目录的 key 保持一致
  let dataFileName = 'data.csv'
  if (uploadedFiles.value.length > 0) {
    const origName = uploadedFiles.value[0].name
    dataFileName = origName.toLowerCase().endsWith('.csv') ? origName : origName.replace(/\.(xlsx|xls)$/i, '.csv')
  } else if (config.value.dataFile) {
    dataFileName = config.value.dataFile
  }

  const modelCol = taylorModelColumn.value || (config.value.dataColumns[0] ?? '')
  const corrCol = taylorCorrColumn.value || ''
  const stdCol = taylorStdColumn.value || ''
  const refStd = Number.isFinite(taylorRefStd.value) ? taylorRefStd.value : 1.0

  // 转义标题中的特殊字符（双引号、反斜杠、换行符）
  const safeTitle = (template.value?.name || config.value.titleText || '泰勒图')
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '')

  // 注意：Python 顶层不能有意外缩进，否则会触发 IndentationError
  const code = `# 自动生成的泰勒图绘图代码
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

DATA_FILE = r"${dataFileName}"
MODEL_COL = r"${modelCol}"
CORR_COL = r"${corrCol}"
STD_COL = r"${stdCol}"
REF_STD = float(${refStd})
TITLE = "${safeTitle}"

def _read_table(path):
    import os
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.xlsx', '.xls']:
        return pd.read_excel(path)
    return pd.read_csv(path)

df = _read_table(DATA_FILE)

if not CORR_COL:
    raise RuntimeError('泰勒图需要选择“相关系数”列')
if MODEL_COL not in df.columns:
    # 兜底：用第一列做模型名
    MODEL_COL = df.columns[0]
if CORR_COL not in df.columns:
    raise RuntimeError(f'找不到相关系数列: {CORR_COL}')

labels = df[MODEL_COL].astype(str).fillna('').to_numpy()
corr = pd.to_numeric(df[CORR_COL], errors='coerce').to_numpy()

if STD_COL and (STD_COL in df.columns):
    std = pd.to_numeric(df[STD_COL], errors='coerce').to_numpy()
else:
    std = np.full_like(corr, REF_STD, dtype=float)

mask = np.isfinite(corr) & np.isfinite(std)
labels = labels[mask]
corr = corr[mask]
std = std[mask]

if len(corr) == 0:
    raise RuntimeError('有效数据为空：请检查相关系数/标准差列是否为数值')

# 相关系数裁剪到 [0, 1]
corr = np.clip(corr, 0.0, 1.0)

fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='polar')
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
ax.set_thetamin(0)
ax.set_thetamax(90)

# 半径范围
rmax = float(max(np.max(std) * 1.25, REF_STD * 2.2, 1.0))
ax.set_rmax(rmax)

# 标准差参考弧线
theta_range = np.linspace(0, np.pi/2, 200)
rticks = []
for v in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
    if v <= rmax + 1e-9:
        rticks.append(v)
        ax.plot(theta_range, np.full_like(theta_range, v), 'gray', alpha=0.25, linewidth=0.8, linestyle='--')
if rticks:
    ax.set_rticks(rticks)
ax.set_rlabel_position(22.5)

# 相关系数径向线 + 标签
for c in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
    t = np.arccos(c)
    ax.plot([t, t], [0, rmax], 'gray', alpha=0.25, linewidth=0.8)
    ax.annotate(f'{c}', xy=(t, rmax * 1.02), fontsize=9, ha='center', va='bottom', alpha=0.75)

# RMSE 圆弧（以参考点 theta=0, r=REF_STD 为圆心的等值线）
for rmse in [0.25, 0.5, 0.75, 1.0]:
    theta_circle = np.linspace(0, np.pi/2, 200)
    r_circle = []
    t_valid = []
    for t in theta_circle:
        # 参考点到任一点的距离（余弦定理）
        r = np.sqrt(REF_STD**2 + rmse**2 - 2*REF_STD*rmse*np.cos(np.pi/2 - t))
        if 0 <= r <= rmax:
            r_circle.append(r)
            t_valid.append(t)
    if len(r_circle) > 0:
        ax.plot(t_valid, r_circle, 'g--', alpha=0.35, linewidth=1)

# 观测值（参考点）：corr=1 -> theta=0
ax.plot(0, REF_STD, 'ko', markersize=12, label='观测值', zorder=6)

# 模型点
palette = ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2', '#DC0000', '#7E6148']
markers = ['o', 's', '^', 'D', 'v', 'p', '*', 'X', 'h']

for i, (name, c, s) in enumerate(zip(labels, corr, std)):
    theta = np.arccos(c)
    color = palette[i % len(palette)]
    marker = markers[i % len(markers)]
    ax.plot(theta, s, marker=marker, color=color, markersize=12,
            markeredgecolor='white', markeredgewidth=1.5, label=str(name), zorder=5)

ax.set_title(TITLE + '\\n(角度=相关系数, 半径=标准差)', fontsize=14, pad=20)
ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.05), frameon=True, fontsize=10)

plt.tight_layout()
plt.savefig('output.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
`
  return code
}

// 运行代码生成图片
async function runCode() {
  // 清理上一次运行结果，避免出现“上一张图 + 本次错误/提示”混杂
  runError.value = ''
  runNotice.value = ''
  resultImage.value = ''

  // 检查是否已上传文件但未分析
  if (uploadedFiles.value.length > 0 && !isDataAnalyzed.value) {
    runError.value = '请先点击"开始分析"按钮分析上传的文件'
    return
  }
  
  // 检查是否有可用数据
  if (uploadedFiles.value.length === 0 && (!template.value?.data_files || template.value.data_files.length === 0)) {
    runError.value = '请先上传数据文件或选择模板数据'
    return
  }
  
  // 检查是否选中了要生成的图表
  if (!isTaylorTemplate.value && selectedPairIndices.value.length === 0) {
    runError.value = '请至少选择一个要生成的图表'
    return
  }
  
  // 如果没有配对列但有数据列，使用前两列
  if (!isTaylorTemplate.value && detectedPairs.value.length === 0 && config.value.dataColumns.length >= 2) {
    detectedPairs.value = [{
      name: `${config.value.dataColumns[0]}_vs_${config.value.dataColumns[1]}`,
      col0: config.value.dataColumns[0],
      col1: config.value.dataColumns[1]
    }]
    config.value.chartCount = 1
    selectedPairIndices.value = [0]
  }
  
  running.value = true
  runError.value = ''
  runNotice.value = ''
  resultImage.value = ''
  
  try {
    const code = generateCode()
    const dataFiles: Record<string, string> = {}
    let actualDataFileName = ''
    
    if (uploadedFiles.value.length > 0) {
      // 使用上传的文件
      for (const item of uploadedFiles.value) {
        // Excel 上传时，我们在前端已转换为 CSV；务必用 .csv 文件名写入临时目录，供 pandas.read_csv 读取
        const safeName = item.name.toLowerCase().endsWith('.csv') ? item.name : item.name.replace(/\.(xlsx|xls)$/i, '.csv')
        dataFiles[safeName] = item.content
        if (!actualDataFileName) {
          actualDataFileName = safeName  // 记录第一个文件的实际名字
        }
      }
    } else if (template.value?.data_files.length) {
      for (const df of template.value.data_files) {
        dataFiles[df.name] = df.content
        if (!actualDataFileName) {
          actualDataFileName = df.name
        }
      }
    }
    
    // 如果生成的代码中文件名不匹配，需要调整
    // 但由于 generateCode 已生成，我们在这里对 dataFiles 的处理应确保能匹配上
    console.log('即将发送的数据文件:', Object.keys(dataFiles))
    console.log('生成的代码:', code.substring(0, 500) + '...')
    
    const { data } = await api.post('/templates/run', {
      code,
      template_id: props.templateId,
      data_files: dataFiles
    })
    
    console.log('后端响应:', data)
    if (data.success) {
      resultImage.value = `data:image/png;base64,${data.image_base64}`
      runNotice.value = '✓ 图表生成成功'
    } else {
      runError.value = data.error || '执行失败'
    }
  } catch (e: any) {
    console.error('执行错误:', e)
    runError.value = e?.response?.data?.detail ?? String(e)
  } finally {
    running.value = false
  }
}

// 下载图片
function downloadImage() {
  if (!resultImage.value) return
  
  const a = document.createElement('a')
  a.href = resultImage.value
  a.download = `${template.value?.name || 'chart'}.png`
  a.click()
}

// 全选/取消全选图表
function toggleSelectAll(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.checked) {
    selectedPairIndices.value = detectedPairs.value.map((_, i) => i)
  } else {
    selectedPairIndices.value = []
  }
}

// 格式化图表名称（去除前缀）
function formatChartName(name: string): string {
  let result = name
  // 去除常见前缀
  for (const prefix of ['PHIT', 'PHI', 'phi', 'model_', 'Model_']) {
    if (result.startsWith(prefix)) {
      result = result.slice(prefix.length)
    }
  }
  // 去除开头的下划线
  return result.replace(/^_+/, '') || name
}

// 监听图形数量变化时自动调整网格（现在由 autoDetectChartCount 处理）
// watch 保留用于手动修改场景
watch(() => config.value.chartCount, (count) => {
  if (count > 0 && gridCapacity.value < count) {
    // 如果当前网格容量不足，自动调整
    updateGridLayout(count)
  }
})

// 监听检测到的配对变化，自动全选并更新布局
watch(detectedPairs, (pairs) => {
  // 默认全选所有检测到的配对
  selectedPairIndices.value = pairs.map((_, i) => i)
  // 更新网格布局
  if (pairs.length > 0) {
    updateGridLayout(pairs.length)
  }
}, { deep: true })

// 监听选择变化，更新网格布局
watch(selectedPairIndices, (indices) => {
  const count = indices.length
  if (count > 0 && gridCapacity.value < count) {
    updateGridLayout(count)
  }
}, { deep: true })

// 监听模板ID变化
watch(() => props.templateId, fetchTemplate, { immediate: true })

// 选择模板数据文件时自动解析（未上传自定义数据时）
watch(() => config.value.dataFile, (name) => {
  if (!name || uploadedFiles.value.length > 0) return
  const df = template.value?.data_files?.find(x => x.name === name)
  if (df) {
    parseDataFile(df.content, df.name)
  }
})
</script>

<template>
  <div class="chart-configurator">
    <!-- 顶部栏 -->
    <div class="config-header">
      <button class="back-btn" @click="emit('back')">
        ← 返回模板库
      </button>
      <div class="template-title">
        <span class="category-tag">{{ template?.category }}</span>
        <h2>{{ template?.name || '加载中...' }}</h2>
      </div>
      <div class="header-actions">
        <button class="btn secondary" @click="downloadImage" :disabled="!resultImage">
          💾 下载图片
        </button>
        <button class="btn primary" @click="runCode" :disabled="running">
          {{ running ? '⏳ 生成中...' : '🎨 生成图表' }}
        </button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="config-main">
      <!-- 左侧：配置面板 -->
      <div class="config-panel">
        <div class="panel-scroll">
          <!-- 数据源配置 -->
          <section class="config-section">
            <h3>📊 数据源</h3>
            
            <div class="form-group">
              <label>选择数据文件</label>
              <select v-model="config.dataFile" class="form-select">
                <option v-for="df in template?.data_files" :key="df.name" :value="df.name">
                  {{ df.name }}
                </option>
              </select>
            </div>
            
            <div class="form-group">
              <label>或上传自定义数据（支持多文件）</label>
              <div class="upload-area">
                <input type="file" accept=".csv,.xlsx,.xls" @change="handleFileUpload" multiple />
                <div class="upload-hint">支持同时选择多个 CSV/Excel 文件</div>
              </div>
              
              <!-- 已上传文件列表 -->
              <div v-if="uploadedFiles.length > 0" class="uploaded-files-section">
                <div class="uploaded-files-list">
                  <div class="list-header">
                    <span>已上传 {{ uploadedFiles.length }} 个文件</span>
                    <span v-if="isDataAnalyzed" class="analyze-status">✅ 已分析</span>
                  </div>
                  <div 
                    v-for="(item, index) in uploadedFiles" 
                    :key="index" 
                    class="uploaded-file-item"
                  >
                    <span class="file-icon">📄</span>
                    <span class="file-name">{{ item.name }}</span>
                    <span class="file-size">{{ (item.file.size / 1024).toFixed(1) }} KB</span>
                    <button 
                      class="remove-btn" 
                      @click="removeUploadedFile(index)"
                      title="删除文件"
                    >
                      ×
                    </button>
                  </div>
                </div>
                
                <!-- 开始分析按钮 -->
                <button 
                  v-if="!isDataAnalyzed"
                  class="analyze-files-btn"
                  @click="analyzeUploadedFiles"
                >
                  🔍 开始分析数据
                </button>
              </div>
            </div>
          </section>

          <!-- 图形数量配置 -->
          <section class="config-section">
            <h3 v-if="!isTaylorTemplate">📐 图形布局</h3>
            <h3 v-else>🧭 泰勒图参数</h3>

            <!-- 泰勒图参数（列映射） -->
            <template v-if="isTaylorTemplate">
              <div class="form-group" v-if="config.dataColumns.length > 0">
                <label>模型名称列（用于图例）</label>
                <select v-model="taylorModelColumn" class="form-select">
                  <option v-for="c in config.dataColumns" :key="c" :value="c">{{ c }}</option>
                </select>
              </div>

              <div class="form-group" v-if="config.dataColumns.length > 0">
                <label>相关系数列（0~1）</label>
                <select v-model="taylorCorrColumn" class="form-select">
                  <option value="">请选择</option>
                  <option v-for="c in config.dataColumns" :key="c" :value="c">{{ c }}</option>
                </select>
              </div>

              <div class="form-group" v-if="config.dataColumns.length > 0">
                <label>标准差列（可选）</label>
                <select v-model="taylorStdColumn" class="form-select">
                  <option value="">(不提供则统一使用参考标准差)</option>
                  <option v-for="c in config.dataColumns" :key="c" :value="c">{{ c }}</option>
                </select>
              </div>

              <div class="form-group">
                <label>参考标准差（观测值）</label>
                <input type="number" v-model.number="taylorRefStd" class="form-input" step="0.01" />
                <div class="upload-hint">若没有标准差列，可保持为 1.0</div>
              </div>
            </template>
            
            <div class="form-group" v-if="!isTaylorTemplate">
              <label>识别到的图形数量</label>
              <div class="detected-count">
                <span class="count-value">{{ detectedPairs.length || '等待数据...' }}</span>
                <span class="count-hint" v-if="detectedPairs.length > 0">
                  (从数据中自动识别)
                </span>
                <span class="count-hint" v-else-if="isDataAnalyzed && config.dataColumns.length > 0">
                  (未识别到配对列，将使用前两列：{{ config.dataColumns[0] }} / {{ config.dataColumns[1] }})
                </span>
              </div>
            </div>

            <!-- 选择要生成的图表 -->
            <div class="form-group" v-if="!isTaylorTemplate && detectedPairs.length > 0">
              <label>选择要生成的图表</label>
              <div class="chart-selection">
                <div class="select-all-row">
                  <label class="checkbox-item">
                    <input 
                      type="checkbox" 
                      :checked="selectedPairIndices.length === detectedPairs.length"
                      :indeterminate="selectedPairIndices.length > 0 && selectedPairIndices.length < detectedPairs.length"
                      @change="toggleSelectAll"
                    />
                    <span>全选 ({{ selectedPairIndices.length }}/{{ detectedPairs.length }})</span>
                  </label>
                </div>
                <div class="chart-list">
                  <label 
                    v-for="(pair, index) in detectedPairs" 
                    :key="index" 
                    class="chart-option"
                    :class="{ selected: selectedPairIndices.includes(index) }"
                  >
                    <input 
                      type="checkbox"
                      :value="index"
                      v-model="selectedPairIndices"
                    />
                    <span class="chart-name">{{ formatChartName(pair.name) }}</span>
                    <span class="chart-cols">{{ pair.col0 }} / {{ pair.col1 }}</span>
                  </label>
                </div>
              </div>
              <div class="selection-hint">
                已选择 {{ selectedPairIndices.length }} 个图表
              </div>
            </div>
            
            <div class="form-group" v-if="!isTaylorTemplate && selectedPairIndices.length > 0">
              <label>网格布局</label>
              <div class="grid-layout-selector">
                <select v-model.number="config.gridRows" class="form-select half">
                  <option v-for="n in maxGridSize" :key="n" :value="n">{{ n }} 行</option>
                </select>
                <span class="multiply">×</span>
                <select v-model.number="config.gridCols" class="form-select half">
                  <option v-for="n in maxGridSize" :key="n" :value="n">{{ n }} 列</option>
                </select>
              </div>
              <div class="layout-hint" :class="{ warning: gridCapacity < effectiveChartCount }">
                <span v-if="gridCapacity >= effectiveChartCount">
                  ✓ 当前布局可容纳 {{ gridCapacity }} 个图表
                </span>
                <span v-else>
                  ⚠️ 布局容量不足！需要至少 {{ effectiveChartCount }} 格
                </span>
              </div>
            </div>
          </section>

          <!-- 数据点样式 -->
          <section class="config-section">
            <h3>🔵 数据点样式</h3>
            
            <div class="form-group">
              <label>形状</label>
              <div class="shape-options">
                <label 
                  v-for="shape in shapeOptions" 
                  :key="shape.value"
                  :class="['shape-option', { active: config.markerShape === shape.value }]"
                >
                  <input 
                    type="radio" 
                    v-model="config.markerShape" 
                    :value="shape.value"
                    hidden
                  />
                  <span class="shape-preview">{{ shape.label.split(' ')[1] }}</span>
                  <span class="shape-name">{{ shape.label.split(' ')[0] }}</span>
                </label>
              </div>
            </div>
            
            <div class="form-group">
              <label>大小: {{ config.markerSize }}px</label>
              <input 
                type="range" 
                v-model.number="config.markerSize" 
                min="2" 
                max="20"
                class="form-range"
              />
            </div>
          </section>

          <!-- 文字显示 -->
          <section class="config-section">
            <h3>📝 文字显示</h3>
            
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input type="checkbox" v-model="config.showTitle" />
                <span>显示标题</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="config.showLabels" />
                <span>显示坐标轴标签</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="config.showLegend" />
                <span>显示图例</span>
              </label>
              <label class="checkbox-item">
                <input type="checkbox" v-model="config.showFormulas" />
                <span>显示公式/注释</span>
              </label>
            </div>
            
            <div v-if="config.showTitle" class="form-group">
              <label>标题文字</label>
              <input 
                type="text" 
                v-model="config.titleText" 
                placeholder="输入图表标题"
                class="form-input"
              />
            </div>
          </section>

          <!-- Colorbar 设置 -->
          <section class="config-section">
            <h3>🌈 颜色条设置</h3>
            
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input type="checkbox" v-model="config.useColorbar" />
                <span>启用颜色条</span>
              </label>
            </div>
            
            <template v-if="config.useColorbar">
              <div class="form-group">
                <label>颜色映射</label>
                <select v-model="config.colormap" class="form-select">
                  <option v-for="cm in colormapOptions" :key="cm.value" :value="cm.value">
                    {{ cm.label }}
                  </option>
                </select>
              </div>
              
              <div class="form-row">
                <div class="form-group half">
                  <label>最小值</label>
                  <input 
                    type="number" 
                    v-model.number="config.colorbarMin" 
                    placeholder="自动"
                    class="form-input"
                  />
                </div>
                <div class="form-group half">
                  <label>最大值</label>
                  <input 
                    type="number" 
                    v-model.number="config.colorbarMax" 
                    placeholder="自动"
                    class="form-input"
                  />
                </div>
              </div>
            </template>
          </section>
        </div>
      </div>

      <!-- 右侧：实时预览 -->
      <div class="preview-section">
        <div class="section-header">
          <span>实时预览</span>
          <span class="hint">调整左侧配置后点击"生成图表"</span>
        </div>
        
        <div class="preview-content">
          <!-- 加载中 -->
          <div v-if="running" class="preview-loading">
            <div class="spinner"></div>
            <p>正在生成图表...</p>
          </div>
          
          <!-- 错误 -->
          <div v-else-if="runError" class="preview-error">
            <div class="error-title">❌ 生成失败</div>
            <pre class="error-detail">{{ runError }}</pre>
          </div>
          
          <!-- 结果图片 -->
          <div v-else-if="resultImage" class="preview-image">
            <div v-if="runNotice" class="preview-notice">{{ runNotice }}</div>
            <img :src="resultImage" alt="Generated Chart" />
          </div>
          
          <!-- 空状态 -->
          <div v-else class="preview-empty">
            <div class="empty-icon">🎨</div>
            <p>配置好参数后</p>
            <p>点击"生成图表"预览效果</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-configurator {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
}

.config-header {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  gap: 16px;
}

.back-btn {
  padding: 8px 14px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #e2e8f0;
  color: #334155;
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
  color: #1e293b;
}

.category-tag {
  padding: 4px 10px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn.primary {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.btn.primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.btn.secondary {
  background: white;
  border: 1px solid #e2e8f0;
  color: #64748b;
}

.btn.secondary:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.config-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.config-panel {
  width: 380px;
  background: white;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.panel-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.config-section {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f1f5f9;
}

.config-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.config-section h3 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.form-select, .form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #334155;
  background: white;
  transition: all 0.2s;
}

.form-select:focus, .form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-select.half, .form-group.half {
  width: calc(50% - 12px);
  display: inline-block;
}

.multiply {
  display: inline-block;
  width: 24px;
  text-align: center;
  color: #94a3b8;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-row .form-group.half {
  flex: 1;
  width: auto;
}

.form-range {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  appearance: none;
  cursor: pointer;
}

.form-range::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
}

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
}

/* 自动识别的图表数量显示 */
.detected-count {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-radius: 10px;
  border: 1px solid #bfdbfe;
}

.count-value {
  font-size: 24px;
  font-weight: 700;
  color: #1d4ed8;
}

.count-hint {
  font-size: 12px;
  color: #64748b;
}

/* 网格布局选择器 */
.grid-layout-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.grid-layout-selector .form-select.half {
  width: auto;
  flex: 1;
}

.layout-hint {
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

.layout-hint.warning {
  background: #fef3c7;
  color: #b45309;
  border-color: #fcd34d;
}

/* 图表选择区域 */
.chart-selection {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
}

.select-all-row {
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
}

.select-all-row .checkbox-item {
  font-weight: 600;
  color: #1e293b;
}

.chart-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.chart-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.chart-option:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.chart-option.selected {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-color: #3b82f6;
}

.chart-option input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #3b82f6;
}

.chart-name {
  font-weight: 600;
  color: #1e293b;
  flex-shrink: 0;
}

.chart-cols {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.selection-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
  text-align: right;
}

.shape-options {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.shape-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 4px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.shape-option:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.shape-option.active {
  border-color: #3b82f6;
  background: #eff6ff;
}

.shape-preview {
  font-size: 20px;
  line-height: 1;
  margin-bottom: 4px;
}

.shape-name {
  font-size: 10px;
  color: #64748b;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-size: 14px;
  color: #475569;
}

.checkbox-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #3b82f6;
  cursor: pointer;
}

.upload-area {
  padding: 16px;
  border: 2px dashed #e2e8f0;
  border-radius: 8px;
  text-align: center;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}

.upload-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
}

/* 已上传文件列表 */
.uploaded-files-section {
  margin-top: 12px;
}

.uploaded-files-list {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  overflow: hidden;
  margin-bottom: 12px;
}

.list-header {
  padding: 8px 12px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.analyze-files-btn {
  width: 100%;
  padding: 12px 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(59, 130, 246, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.analyze-files-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(59, 130, 246, 0.4);
}

.analyze-files-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 6px rgba(59, 130, 246, 0.25);
}

.analyze-status {
  padding: 4px 10px;
  background: #dcfce7;
  color: #15803d;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.uploaded-file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.2s;
}

.uploaded-file-item:last-child {
  border-bottom: none;
}

.uploaded-file-item:hover {
  background: #f8fafc;
}

.file-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.file-name {
  flex: 1;
  font-size: 13px;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 12px;
  color: #94a3b8;
  flex-shrink: 0;
}

.remove-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #94a3b8;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

.preview-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 400px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
}

.section-header .hint {
  font-size: 12px;
  color: #94a3b8;
  font-weight: normal;
}

.preview-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  overflow: auto;
}

.preview-loading {
  text-align: center;
  color: #64748b;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.preview-error {
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
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  font-size: 12px;
  color: #b91c1c;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow: auto;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
}

.preview-notice {
  margin-bottom: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #ecfdf5;
  border: 1px solid #bbf7d0;
  color: #166534;
  font-size: 13px;
  font-weight: 600;
}

.preview-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.preview-empty {
  text-align: center;
  color: #94a3b8;
}

.empty-icon {
  font-size: 72px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.preview-empty p {
  margin: 4px 0;
  font-size: 15px;
}
</style>

