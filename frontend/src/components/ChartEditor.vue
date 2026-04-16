<template>
  <div class="chart-editor">
    <!-- Header -->
    <header class="editor-header">
      <button class="back-btn" @click="$emit('back')">
        <span class="icon">←</span> 返回模板库
      </button>
      <div class="template-info">
        <span class="template-name">{{ template?.name || '图表编辑器' }}</span>
        <span class="category-badge" v-if="template?.category">{{ template.category }}</span>
      </div>
      <div class="header-actions">
        <button class="btn-secondary" @click="resetConfig">重置配置</button>
        <button class="btn-primary" @click="runChart" :disabled="!canRun || isRunning">
          <span v-if="isRunning" class="spinner"></span>
          {{ isRunning ? '生成中...' : '▶ 生成图表' }}
        </button>
      </div>
    </header>

    <div class="editor-body">
      <!-- Left Panel: Configuration -->
      <aside class="config-panel">
        <!-- Step 1: Upload Data -->
        <section class="config-section">
          <h3 class="section-title">
            <span class="step-num">1</span>
            数据文件
          </h3>
          <div 
            class="upload-zone"
            :class="{ 'has-file': uploadedFile, 'drag-over': isDragging }"
            @drop.prevent="handleDrop"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @click="triggerFileInput"
          >
            <input 
              ref="fileInput" 
              type="file" 
              accept=".csv,.xlsx,.xls"
              @change="handleFileSelect"
              hidden
            />
            <template v-if="uploadedFile">
              <div class="file-info">
                <span class="file-icon">📊</span>
                <div class="file-details">
                  <span class="file-name">{{ uploadedFile.name }}</span>
                  <span class="file-meta" v-if="parsedData">
                    {{ parsedData.row_count }} 行 × {{ parsedData.columns.length }} 列
                  </span>
                </div>
                <button class="remove-file" @click.stop="removeFile">✕</button>
              </div>
            </template>
            <template v-else>
              <span class="upload-icon">📁</span>
              <span class="upload-text">拖拽文件到此处，或点击选择</span>
              <span class="upload-hint">支持 .csv, .xlsx, .xls 格式</span>
            </template>
          </div>
        </section>

        <!-- Step 2: Data Columns (不显示于子图模板、三元图模板和模型预测对比图模板) -->
        <section class="config-section" v-if="parsedData && !isSubplotTemplate && !isTernaryTemplate && !isModelCompareTemplate && !isStackedBarTemplate && !isCorrelationScatterTemplate && !isMatrixBubbleTemplate && !isGeneralHeatmapTemplate && !isGeneralBoxplotTemplate && !isSignificanceBoxplotTemplate && !isJointPlotTemplate">
          <h3 class="section-title">
            <span class="step-num">2</span>
            数据列映射
          </h3>
          
          <!-- 自动识别模板显示提示 -->
          <div v-if="isAutoDetectTemplate" class="auto-detect-info">
            <div class="auto-detect-icon">🔍</div>
            <div class="auto-detect-text">
              <strong>自动识别数据配对</strong>
              <p>本模板将根据列名自动识别数据配对（如 XXX_0/XXX_1 模式）</p>
            </div>
            <div class="detected-pairs">
              <label 
                v-for="pair in detectedPairs" 
                :key="pair.name"
                class="pair-option"
                :class="{ selected: chartConfig.selected_pairs.includes(pair.name) }"
              >
                <input 
                  type="checkbox" 
                  :value="pair.name"
                  v-model="chartConfig.selected_pairs"
                />
                <span class="pair-name">{{ pair.name }}</span>
                <span class="pair-cols">{{ pair.x_col }} ↔ {{ pair.y_col }}</span>
              </label>
            </div>
            <p class="pair-hint" v-if="detectedPairs.length > 0">
              已选择 {{ chartConfig.selected_pairs.length }} / {{ detectedPairs.length }} 个模型
            </p>
          </div>
          
          <!-- 其他模板显示手动选择 -->
          <template v-else>
            <div class="form-group">
              <label>X 轴数据列</label>
              <select v-model="chartConfig.x_column" class="form-select">
                <option value="">-- 选择列 --</option>
                <option 
                  v-for="col in parsedData.columns" 
                  :key="col.name"
                  :value="col.name"
                >
                  {{ col.name }} ({{ col.is_numeric ? '数值' : '文本' }})
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>Y 轴数据列 (可多选)</label>
              <div class="column-picker">
                <label 
                  v-for="col in numericColumns" 
                  :key="col.name"
                  class="column-option"
                  :class="{ selected: chartConfig.y_columns.includes(col.name) }"
                >
                  <input 
                    type="checkbox" 
                    :value="col.name"
                    v-model="chartConfig.y_columns"
                  />
                  <span class="col-name">{{ col.name }}</span>
                  <span class="col-sample">{{ formatSample(col.sample_values) }}</span>
                </label>
              </div>
            </div>

            <div class="form-group">
              <label>分组列 (可选)</label>
              <select v-model="chartConfig.group_column" class="form-select">
                <option value="">-- 无分组 --</option>
                <option 
                  v-for="col in parsedData.columns" 
                  :key="col.name"
                  :value="col.name"
                >
                  {{ col.name }} ({{ col.unique_count }} 个唯一值)
                </option>
              </select>
            </div>
          </template>
        </section>

        <!-- Step 3: Visual Style -->
        <section class="config-section" v-if="parsedData">
          <h3 class="section-title">
            <span class="step-num">3</span>
            图表样式
          </h3>

          <!-- 散点样式和线条样式（3D曲面图等不显示） -->
          <template v-if="showMarkerOptions || isMatrixBubbleTemplate">
            <div class="form-row">
              <div class="form-group half">
                <label>{{ isMatrixBubbleTemplate ? '气泡形状' : '散点样式' }}</label>
                <div class="marker-picker">
                  <button 
                    v-for="marker in (isMatrixBubbleTemplate ? bubbleMarkerOptions : markerOptions)"
                    :key="marker.value"
                    class="marker-btn"
                    :class="{ active: (isMatrixBubbleTemplate ? chartConfig.bubble_shape : chartConfig.marker_style) === marker.value }"
                    @click="isMatrixBubbleTemplate ? (chartConfig.bubble_shape = marker.value) : (chartConfig.marker_style = marker.value)"
                    :title="marker.label"
                  >
                    {{ marker.icon }}
                  </button>
                </div>
              </div>
              <div class="form-group half">
                <label>{{ isMatrixBubbleTemplate ? '气泡大小' : '散点大小' }}</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.marker_size"
                  :min="isMatrixBubbleTemplate ? 50 : 4" 
                  :max="isMatrixBubbleTemplate ? 200 : 20" 
                  :step="isMatrixBubbleTemplate ? 10 : 1"
                  class="form-range"
                />
                <span class="range-value">{{ isMatrixBubbleTemplate ? chartConfig.marker_size : chartConfig.marker_size + 'px' }}</span>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group half">
                <label>{{ isMatrixBubbleTemplate ? '网格线样式' : '线条样式' }}</label>
                <select v-model="chartConfig.line_style" class="form-select">
                  <option value="solid">实线 ───</option>
                  <option value="dashed">虚线 - - -</option>
                  <option value="dotted">点线 ·····</option>
                  <option v-if="!isMatrixBubbleTemplate" value="dashdot">点划线 -·-·</option>
                  <option v-if="isMatrixBubbleTemplate" value="none">无网格</option>
                </select>
              </div>
              <div class="form-group half" v-if="!isMatrixBubbleTemplate">
                <label>线条粗细</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.line_width"
                  min="0.5" 
                  max="5" 
                  step="0.5"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.line_width }}px</span>
              </div>
              <div class="form-group half" v-if="isMatrixBubbleTemplate">
                <label>透明度</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.bubble_alpha"
                  min="0.3" 
                  max="1" 
                  step="0.1"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.bubble_alpha }}</span>
              </div>
            </div>

            <!-- 矩阵气泡图额外选项 -->
            <div class="form-row checkboxes" v-if="isMatrixBubbleTemplate">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_size_legend" />
                显示大小图例
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_colorbar" />
                显示颜色条
              </label>
            </div>
          </template>

          <!-- 柱形图专属选项 -->
          <template v-if="showBarChartOptions">
            <!-- 堆积柱形图专属选项 -->
            <template v-if="isStackedBarTemplate">
              <div class="form-row checkboxes">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="chartConfig.show_values" />
                  显示数值标签
                </label>
              </div>
              <div class="form-row">
                <div class="form-group half">
                  <label>柱子宽度</label>
                  <input 
                    type="range" 
                    v-model.number="chartConfig.bar_width"
                    min="0.3" 
                    max="1" 
                    step="0.1"
                    class="form-range"
                  />
                  <span class="range-value">{{ chartConfig.bar_width }}</span>
                </div>
              </div>
            </template>
            
            <!-- 通用柱状图专属选项 -->
            <template v-else-if="isGeneralBarTemplate">
              <div class="form-row">
                <div class="form-group half">
                  <label>柱子宽度</label>
                  <input 
                    type="range" 
                    v-model.number="chartConfig.bar_width"
                    min="0.3" 
                    max="1" 
                    step="0.1"
                    class="form-range"
                  />
                  <span class="range-value">{{ chartConfig.bar_width }}</span>
                </div>
                <div class="form-group half">
                  <label>透明度</label>
                  <input 
                    type="range" 
                    v-model.number="chartConfig.bubble_alpha"
                    min="0.3" 
                    max="1" 
                    step="0.1"
                    class="form-range"
                  />
                  <span class="range-value">{{ chartConfig.bubble_alpha }}</span>
                </div>
              </div>
              <div class="form-row checkboxes">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="chartConfig.show_values" />
                  显示数值标签
                </label>
              </div>
            </template>
            
            <!-- 误差柱形图专属选项 -->
            <template v-else>
              <div class="form-row checkboxes">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="chartConfig.show_error" />
                  显示误差线
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="chartConfig.show_points" />
                  显示数据点
                </label>
              </div>

              <div class="form-row" v-if="chartConfig.show_error">
                <div class="form-group half">
                  <label>误差类型</label>
                  <select v-model="chartConfig.error_type" class="form-select">
                    <option value="sd">标准差 (SD)</option>
                    <option value="se">标准误 (SE)</option>
                    <option value="ci">置信区间 (95% CI)</option>
                  </select>
                </div>
                <div class="form-group half">
                  <label>柱子宽度</label>
                  <input 
                    type="range" 
                    v-model.number="chartConfig.bar_width"
                    min="0.3" 
                    max="1" 
                    step="0.1"
                    class="form-range"
                  />
                  <span class="range-value">{{ chartConfig.bar_width }}</span>
                </div>
              </div>

              <div class="form-row" v-if="chartConfig.show_points">
                <div class="form-group half">
                  <label>数据点大小</label>
                  <input 
                    type="range" 
                    v-model.number="chartConfig.point_size"
                    min="2" 
                    max="12" 
                    step="1"
                    class="form-range"
                  />
                  <span class="range-value">{{ chartConfig.point_size }}px</span>
                </div>
              </div>
            </template>
          </template>

          <!-- 云雨图/小提琴图专属选项 -->
          <template v-if="isRaincloudTemplate">
            <!-- 云雨图显示样式选择 -->
            <div class="form-group" v-if="isCloudRainTemplate">
              <label>云雨图样式</label>
              <div class="raincloud-style-picker">
                <label 
                  v-for="style in raincloudStyles"
                  :key="style.value"
                  class="style-option"
                  :class="{ selected: chartConfig.raincloud_style === style.value }"
                >
                  <input 
                    type="radio" 
                    :value="style.value"
                    v-model="chartConfig.raincloud_style"
                    hidden
                  />
                  <span class="style-num">{{ style.value }}</span>
                  <span class="style-desc">{{ style.desc }}</span>
                </label>
              </div>
            </div>
            
            <!-- 普通小提琴图显示简单选项 -->
            <div class="form-row checkboxes" v-if="!isCloudRainTemplate">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_box" />
                显示箱线图
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_points" />
                显示散点
              </label>
            </div>
            
            <div class="form-row" v-if="!isCloudRainTemplate && chartConfig.show_points">
              <div class="form-group half">
                <label>散点大小</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.point_size"
                  min="2" 
                  max="12" 
                  step="1"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.point_size }}px</span>
              </div>
            </div>
          </template>

          <!-- 子图/axes模板专属选项 -->
          <template v-if="isSubplotTemplate">
            <div class="form-row">
              <div class="form-group half">
                <label>子图数量</label>
                <select v-model.number="chartConfig.n_subplots" class="form-select">
                  <option :value="2">2 个子图</option>
                  <option :value="3">3 个子图</option>
                  <option :value="4">4 个子图</option>
                </select>
              </div>
              <div class="form-group half">
                <label>布局方式</label>
                <select v-model="chartConfig.subplot_layout" class="form-select">
                  <option value="vertical">垂直排列</option>
                  <option value="horizontal">水平排列</option>
                </select>
              </div>
            </div>
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_colorbar" />
                显示颜色条
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.share_colorbar" />
                共享颜色条
              </label>
            </div>
          </template>

          <!-- 三元图专属选项 -->
          <template v-if="isTernaryTemplate">
            <!-- 三元密度图专属选项 -->
            <template v-if="isTernaryDensityTemplate">
              <div class="form-row">
                <div class="form-group third">
                  <label>顶部标签</label>
                  <input 
                    type="text" 
                    v-model="chartConfig.z_label"
                    class="form-input"
                    placeholder="SiO2"
                  />
                </div>
                <div class="form-group third">
                  <label>左边标签</label>
                  <input 
                    type="text" 
                    v-model="chartConfig.y_label"
                    class="form-input"
                    placeholder="MgO"
                  />
                </div>
                <div class="form-group third">
                  <label>底边标签</label>
                  <input 
                    type="text" 
                    v-model="chartConfig.x_label"
                    class="form-input"
                    placeholder="TiO2"
                  />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group half">
                  <label>颜色条位置</label>
                  <select v-model="chartConfig.colorbar_position" class="form-select">
                    <option value="right">右侧（垂直）</option>
                    <option value="bottom">底部（水平）</option>
                  </select>
                </div>
                <div class="form-group half">
                  <label>密度平滑度</label>
                  <input 
                    type="range" 
                    v-model.number="chartConfig.density_sigma"
                    min="1" 
                    max="5" 
                    step="0.5"
                    class="form-range"
                  />
                  <span class="range-value">{{ chartConfig.density_sigma }}</span>
                </div>
              </div>
              <div class="form-row checkboxes">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="chartConfig.show_scatter" />
                  显示散点
                </label>
                <label class="checkbox-label">
                  <input type="checkbox" v-model="chartConfig.show_grid" />
                  显示网格线
                </label>
              </div>
              <div class="form-row" v-if="chartConfig.show_scatter">
                <div class="form-group half">
                  <label>散点颜色</label>
                  <input 
                    type="color" 
                    v-model="chartConfig.scatter_color"
                    class="color-input"
                  />
                </div>
                <div class="form-group half">
                  <label>散点大小</label>
                  <input 
                    type="range" 
                    v-model.number="chartConfig.marker_size"
                    min="2" 
                    max="12" 
                    step="1"
                    class="form-range"
                  />
                  <span class="range-value">{{ chartConfig.marker_size }}px</span>
                </div>
              </div>
            </template>
            
            <!-- 普通三元图选项 -->
            <template v-else>
              <div class="form-group">
                <label>绑图模式</label>
                <select v-model="chartConfig.ternary_mode" class="form-select">
                  <option value="group">分组散点（按类别着色）</option>
                  <option value="color">颜色映射（按数值分档）</option>
                </select>
              </div>
              <div class="form-row">
                <div class="form-group third">
                  <label>底边标签</label>
                  <input 
                    type="text" 
                    v-model="chartConfig.x_label"
                    class="form-input"
                    placeholder="Variable 1"
                  />
                </div>
                <div class="form-group third">
                  <label>左边标签</label>
                  <input 
                    type="text" 
                    v-model="chartConfig.y_label"
                    class="form-input"
                    placeholder="Variable 2"
                  />
                </div>
                <div class="form-group third">
                  <label>右边标签</label>
                  <input 
                    type="text" 
                    v-model="chartConfig.z_label"
                    class="form-input"
                    placeholder="Variable 3"
                  />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group half">
                  <label>散点大小</label>
                  <input 
                    type="range" 
                    v-model.number="chartConfig.marker_size"
                    min="20" 
                    max="200" 
                    step="10"
                    class="form-range"
                  />
                  <span class="range-value">{{ chartConfig.marker_size }}</span>
                </div>
              </div>
            </template>
          </template>

          <!-- 模型预测对比图专属选项 -->
          <template v-if="isModelCompareTemplate">
            <div class="form-row">
              <div class="form-group half">
                <label>真实值颜色</label>
                <input 
                  type="color" 
                  v-model="chartConfig.true_color"
                  class="color-input"
                />
              </div>
              <div class="form-group half">
                <label>预测值颜色</label>
                <input 
                  type="color" 
                  v-model="chartConfig.pred_color"
                  class="color-input"
                />
              </div>
            </div>
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_metrics" />
                显示R²和MAE指标
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.invert_y" />
                Y轴反向（深度递增）
              </label>
            </div>
          </template>

          <!-- 相关性散点图专属选项 -->
          <template v-if="isCorrelationScatterTemplate">
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_error" />
                显示误差线
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_diagonal" />
                显示1:1对角线
              </label>
            </div>
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_r2" />
                显示R²值
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_regression" />
                显示回归方程
              </label>
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label>散点大小</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.marker_size"
                  min="4" 
                  max="16" 
                  step="1"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.marker_size }}px</span>
              </div>
            </div>
          </template>

          <!-- 泰勒图专属选项 -->
          <template v-if="isTaylorTemplate">
            <div class="form-row">
              <div class="form-group half">
                <label>参考标准差</label>
                <input 
                  type="number" 
                  v-model.number="chartConfig.ref_std"
                  min="0.5" 
                  max="20" 
                  step="0.5"
                  class="form-input"
                  placeholder="5.0"
                />
              </div>
              <div class="form-group half">
                <label>标记大小</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.marker_size"
                  min="6" 
                  max="24" 
                  step="2"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.marker_size }}px</span>
              </div>
            </div>
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_rmsd" />
                显示RMSD等值线
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_labels" />
                显示数据点标签
              </label>
            </div>
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.use_different_markers" />
                使用不同标记区分模型
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_colorbar" />
                显示颜色映射条
              </label>
            </div>
          </template>

          <!-- 通用热力图专属选项 -->
          <template v-if="isGeneralHeatmapTemplate">
            <div class="form-row">
              <div class="form-group half">
                <label>热力图模式</label>
                <select v-model="chartConfig.heatmap_mode" class="form-select">
                  <option value="correlation">相关性矩阵</option>
                  <option value="matrix">原始数据矩阵</option>
                </select>
              </div>
              <div class="form-group half">
                <label>数值精度</label>
                <select v-model="chartConfig.value_format" class="form-select">
                  <option value=".1f">1位小数</option>
                  <option value=".2f">2位小数</option>
                  <option value=".3f">3位小数</option>
                  <option value=".0f">整数</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label>字体大小</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.font_size"
                  min="6" 
                  max="16" 
                  step="1"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.font_size }}px</span>
              </div>
            </div>
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_values" />
                显示数值
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_colorbar" />
                显示颜色条
              </label>
            </div>
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.square_cells" />
                正方形单元格
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.center_zero" />
                颜色中心为0
              </label>
            </div>
          </template>

          <!-- 显著性标注箱线图专属选项 -->
          <template v-if="isSignificanceBoxplotTemplate">
            <div class="form-row">
              <div class="form-group half">
                <label>显著性检验方法</label>
                <select v-model="chartConfig.test_method" class="form-select">
                  <option value="mww">Mann-Whitney U</option>
                  <option value="ttest">t-test</option>
                </select>
              </div>
              <div class="form-group half">
                <label>箱子宽度</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.box_width"
                  min="0.3" 
                  max="0.9" 
                  step="0.1"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.box_width }}</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label>散点大小</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.marker_size"
                  min="4" 
                  max="16" 
                  step="1"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.marker_size }}px</span>
              </div>
              <div class="form-group half">
                <label>散点透明度</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.point_alpha"
                  min="0.3" 
                  max="1" 
                  step="0.1"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.point_alpha }}</span>
              </div>
            </div>
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_points" />
                显示数据散点
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_significance" />
                显示显著性标注
              </label>
            </div>
          </template>

          <!-- 通用箱线图专属选项 -->
          <template v-if="isGeneralBoxplotTemplate">
            <div class="form-row">
              <div class="form-group half">
                <label>箱子宽度</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.box_width"
                  min="0.3" 
                  max="0.9" 
                  step="0.1"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.box_width }}</span>
              </div>
              <div class="form-group half">
                <label>透明度</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.box_alpha"
                  min="0.3" 
                  max="1" 
                  step="0.1"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.box_alpha }}</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label>中位数线宽</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.median_width"
                  min="1" 
                  max="4" 
                  step="0.5"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.median_width }}px</span>
              </div>
              <div class="form-group half">
                <label>方向</label>
                <select v-model="chartConfig.orient" class="form-select">
                  <option value="vertical">垂直</option>
                  <option value="horizontal">水平</option>
                </select>
              </div>
            </div>
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_outliers" />
                显示异常值
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_notch" />
                显示缺口
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_means" />
                显示均值
              </label>
            </div>
          </template>

          <!-- 边际组合图/相关性矩阵图专属选项 -->
          <template v-if="isJointPlotTemplate">
            <div class="form-row">
              <div class="form-group half">
                <label>矩阵样式</label>
                <select v-model="chartConfig.matrix_style" class="form-select">
                  <option value="circle">圆形气泡</option>
                  <option value="square">方形气泡</option>
                  <option value="heatmap">热力图</option>
                  <option value="values">纯数值</option>
                </select>
              </div>
              <div class="form-group half">
                <label>显示模式</label>
                <select v-model="chartConfig.display_mode" class="form-select">
                  <option value="full">完整矩阵</option>
                  <option value="lower">下三角</option>
                  <option value="upper">上三角</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label>数值精度</label>
                <select v-model="chartConfig.value_format" class="form-select">
                  <option value=".1f">1位小数</option>
                  <option value=".2f">2位小数</option>
                  <option value=".3f">3位小数</option>
                </select>
              </div>
              <div class="form-group half">
                <label>字体大小</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.font_size"
                  min="6" 
                  max="14" 
                  step="1"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.font_size }}px</span>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group half">
                <label>网格线宽</label>
                <input 
                  type="range" 
                  v-model.number="chartConfig.grid_width"
                  min="0.5" 
                  max="3" 
                  step="0.5"
                  class="form-range"
                />
                <span class="range-value">{{ chartConfig.grid_width }}px</span>
              </div>
            </div>
            <div class="form-row checkboxes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_values" />
                显示数值
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="chartConfig.show_colorbar" />
                显示颜色条
              </label>
            </div>
          </template>

          <div class="form-group">
            <label>配色方案</label>
            <div class="colormap-picker">
              <button 
                v-for="cm in colormapOptions"
                :key="cm.value"
                class="colormap-btn"
                :class="{ active: chartConfig.colormap === cm.value }"
                @click="chartConfig.colormap = cm.value"
                :style="{ background: cm.gradient }"
                :title="cm.label"
              ></button>
            </div>
          </div>
        </section>

        <!-- Step 4: Labels & Layout -->
        <section class="config-section" v-if="parsedData">
          <h3 class="section-title">
            <span class="step-num">4</span>
            标签与布局
          </h3>

          <div class="form-group">
            <label>图表标题</label>
            <input 
              type="text" 
              v-model="chartConfig.title"
              class="form-input"
              placeholder="输入图表标题"
            />
          </div>

          <div class="form-row">
            <div class="form-group half">
              <label>X 轴标签</label>
              <input 
                type="text" 
                v-model="chartConfig.x_label"
                class="form-input"
                placeholder="X轴"
              />
            </div>
            <div class="form-group half">
              <label>Y 轴标签</label>
              <input 
                type="text" 
                v-model="chartConfig.y_label"
                class="form-input"
                placeholder="Y轴"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group half">
              <label>图表宽度</label>
              <input 
                type="number" 
                v-model.number="chartConfig.fig_width"
                class="form-input"
                min="6"
                max="20"
                step="0.5"
              />
            </div>
            <div class="form-group half">
              <label>图表高度</label>
              <input 
                type="number" 
                v-model.number="chartConfig.fig_height"
                class="form-input"
                min="4"
                max="16"
                step="0.5"
              />
            </div>
          </div>
        </section>

        <!-- Data Preview -->
        <section class="config-section" v-if="parsedData">
          <h3 class="section-title collapsed-title" @click="showDataPreview = !showDataPreview">
            <span class="collapse-icon">{{ showDataPreview ? '▼' : '▶' }}</span>
            数据预览
          </h3>
          <div v-if="showDataPreview" class="data-preview">
            <table class="preview-table">
              <thead>
                <tr>
                  <th v-for="col in parsedData.columns" :key="col.name">{{ col.name }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in parsedData.preview" :key="idx">
                  <td v-for="col in parsedData.columns" :key="col.name">
                    {{ row[col.name] }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </aside>

      <!-- Main Area: Chart Preview -->
      <main class="preview-panel">
        <div class="preview-container" v-if="resultImage">
          <div class="preview-toolbar">
            <button class="toolbar-btn" @click="downloadImage" title="下载图片">
              📥 下载
            </button>
            <button class="toolbar-btn" @click="zoomIn" title="放大">➕</button>
            <button class="toolbar-btn" @click="zoomOut" title="缩小">➖</button>
            <button class="toolbar-btn" @click="resetZoom" title="重置">🔄</button>
            <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
          </div>
          <div class="preview-scroll" ref="previewScroll">
            <img 
              :src="resultImage" 
              alt="生成的图表"
              class="result-image"
              :style="{ transform: `scale(${zoomLevel})` }"
            />
          </div>
        </div>
        <div class="preview-placeholder" v-else>
          <template v-if="isRunning">
            <div class="loading-animation">
              <div class="loading-spinner"></div>
              <p>正在生成图表...</p>
            </div>
          </template>
          <template v-else-if="errorMessage">
            <div class="error-display">
              <span class="error-icon">⚠️</span>
              <h3>生成失败</h3>
              <pre class="error-message">{{ errorMessage }}</pre>
              <button class="btn-secondary" @click="errorMessage = ''">关闭</button>
            </div>
          </template>
          <template v-else>
            <div class="placeholder-content">
              <span class="placeholder-icon">📈</span>
              <h3>图表预览区域</h3>
              <p v-if="!uploadedFile">请先上传数据文件</p>
              <p v-else-if="!isAutoDetectTemplate && !chartConfig.y_columns.length">请选择 Y 轴数据列</p>
              <p v-else>配置完成后，点击"生成图表"按钮</p>
            </div>
          </template>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface ColumnInfo {
  name: string
  dtype: string
  sample_values: any[]
  is_numeric: boolean
  unique_count: number
}

interface ParsedData {
  filename: string
  row_count: number
  columns: ColumnInfo[]
  preview: Record<string, any>[]
}

interface TemplateMeta {
  id: string
  name: string
  category: string
  tags: string[]
  rel_dir: string
  rel_main: string
  thumbnail?: string
}

interface ChartConfig {
  x_column: string
  y_columns: string[]
  group_column: string
  marker_style: string
  marker_size: number
  line_style: string
  line_width: number
  colors: string[]
  colormap: string
  title: string
  x_label: string
  y_label: string
  show_legend: boolean
  show_grid: boolean
  fig_width: number
  fig_height: number
  dpi: number
  selected_pairs: string[]  // 选中的模型配对名称
  // 柱形图专属配置
  show_points: boolean      // 是否显示数据点
  show_error: boolean       // 是否显示误差线
  error_type: string        // 误差类型: sd, se, ci
  bar_width: number         // 柱子宽度
  point_size: number        // 数据点大小
  // 云雨图/小提琴图专属配置
  raincloud_style: number   // 云雨图样式 1-6
  show_box: boolean         // 是否显示箱线图
  // 子图模板专属配置
  n_subplots: number        // 子图数量
  subplot_layout: string    // 子图布局: vertical, horizontal
  show_colorbar: boolean    // 显示colorbar
  share_colorbar: boolean   // 共享colorbar
  // 三元图专属配置
  ternary_mode: string      // 三元图模式: group, color
  z_label: string           // 第三个轴标签
  // 模型预测对比图专属配置
  true_color: string        // 真实值颜色
  pred_color: string        // 预测值颜色
  show_metrics: boolean     // 显示R²和MAE指标
  invert_y: boolean         // Y轴反向
  // 堆积柱形图专属配置
  show_values: boolean      // 显示数值标签
  // 相关性散点图专属配置
  show_regression: boolean  // 显示回归线和方程
  show_r2: boolean          // 显示R²值
  show_diagonal: boolean    // 显示1:1对角线
  // 矩阵气泡图专属配置
  bubble_shape: string      // 气泡形状: circle, square
  show_size_legend: boolean // 显示大小图例
  bubble_alpha: number      // 气泡透明度
  // 泰勒图专属配置
  show_rmsd: boolean        // 显示RMSD等值线
  show_labels: boolean      // 显示数据点标签
  use_different_markers: boolean  // 使用不同标记区分模型
  ref_std: number           // 参考标准差
  // 三元密度图专属配置
  show_scatter: boolean     // 显示散点
  scatter_color: string     // 散点颜色
  colorbar_position: string // 颜色条位置: right, bottom
  density_sigma: number     // 密度平滑系数
  // 通用热力图专属配置
  heatmap_mode: string      // 热力图模式: correlation, matrix
  square_cells: boolean     // 正方形单元格
  center_zero: boolean      // 颜色中心为0
  value_format: string      // 数值格式
  font_size: number         // 数值字体大小
  // 显著性箱线图专属配置
  test_method: string       // 检验方法: ttest, mww
  show_significance: boolean // 显示显著性标注
  box_width: number         // 箱子宽度
  point_alpha: number       // 散点透明度
  jitter_amount: number     // 散点抖动量
  // 通用箱线图专属配置
  box_alpha: number         // 箱子透明度
  show_outliers: boolean    // 显示异常值
  show_notch: boolean       // 显示缺口
  show_means: boolean       // 显示均值
  median_width: number      // 中位数线宽度
  orient: string            // 方向: vertical, horizontal
  // 边际组合图/相关性矩阵图专属配置
  matrix_style: string      // 矩阵样式: circle, square, heatmap, values
  display_mode: string      // 显示模式: full, lower, upper
  grid_width: number        // 网格线宽
}

const props = defineProps<{
  template: TemplateMeta | null
}>()

const emit = defineEmits<{
  back: []
}>()

// State
const fileInput = ref<HTMLInputElement>()
const uploadedFile = ref<File | null>(null)
const parsedData = ref<ParsedData | null>(null)
const isDragging = ref(false)
const isRunning = ref(false)
const resultImage = ref<string>('')
const errorMessage = ref('')
const showDataPreview = ref(false)
const zoomLevel = ref(1)
const previewScroll = ref<HTMLElement>()

// Default configuration
const defaultConfig: ChartConfig = {
  x_column: '',
  y_columns: [],
  group_column: '',
  marker_style: 'circle',
  marker_size: 8,
  line_style: 'solid',
  line_width: 1.5,
  colors: [],  // 空数组，让 colormap 生效
  colormap: 'jet',
  title: '',
  x_label: '',
  y_label: '',
  show_legend: true,
  show_grid: true,
  fig_width: 10,
  fig_height: 8,
  dpi: 150,
  selected_pairs: [],
  // 柱形图专属
  show_points: true,
  show_error: true,
  error_type: 'sd',
  bar_width: 0.8,
  point_size: 5,
  // 云雨图/小提琴图专属
  raincloud_style: 1,
  show_box: true,
  // 子图模板专属
  n_subplots: 2,
  subplot_layout: 'vertical',
  show_colorbar: true,
  share_colorbar: true,
  // 三元图专属
  ternary_mode: 'group',
  z_label: 'Variable 3',
  // 模型预测对比图专属
  true_color: '#0000FF',
  pred_color: '#FF0000',
  show_metrics: true,
  invert_y: true,
  // 堆积柱形图专属
  show_values: true,
  // 相关性散点图专属
  show_regression: true,
  show_r2: true,
  show_diagonal: true,
  // 矩阵气泡图专属
  bubble_shape: 'circle',
  show_size_legend: true,
  bubble_alpha: 0.9,
  // 泰勒图专属
  show_rmsd: true,
  show_labels: true,
  use_different_markers: true,
  ref_std: 5.0,
  // 三元密度图专属
  show_scatter: true,
  scatter_color: '#1f4e79',
  colorbar_position: 'right',
  density_sigma: 2,
  // 通用热力图专属
  heatmap_mode: 'correlation',
  square_cells: true,
  center_zero: true,
  value_format: '.2f',
  font_size: 10,
  // 显著性箱线图专属
  test_method: 'mww',
  show_significance: true,
  box_width: 0.6,
  point_alpha: 0.7,
  jitter_amount: 0.15,
  // 通用箱线图专属
  box_alpha: 0.8,
  show_outliers: true,
  show_notch: false,
  show_means: false,
  median_width: 2,
  orient: 'vertical',
  // 边际组合图/相关性矩阵图专属
  matrix_style: 'circle',
  display_mode: 'full',
  grid_width: 1.5
}

const chartConfig = ref<ChartConfig>({ ...defaultConfig })

// Marker options
const markerOptions = [
  { value: 'circle', icon: '●', label: '圆形' },
  { value: 'square', icon: '■', label: '方形' },
  { value: 'diamond', icon: '◆', label: '菱形' },
  { value: 'triangle', icon: '▲', label: '三角形' },
  { value: 'star', icon: '★', label: '星形' },
  { value: 'plus', icon: '+', label: '加号' },
  { value: 'x', icon: '×', label: '叉号' }
]

// 矩阵气泡图的形状选项
const bubbleMarkerOptions = [
  { value: 'circle', icon: '●', label: '圆形' },
  { value: 'square', icon: '■', label: '方形' },
  { value: 'diamond', icon: '◆', label: '菱形' },
  { value: 'triangle', icon: '▲', label: '三角形' }
]

// Colormap options
const colormapOptions = [
  { value: 'jet', label: 'Jet', gradient: 'linear-gradient(90deg, #000080, #0000ff, #00ffff, #00ff00, #ffff00, #ff0000, #800000)' },
  { value: 'viridis', label: 'Viridis', gradient: 'linear-gradient(90deg, #440154, #31688e, #35b779, #fde725)' },
  { value: 'plasma', label: 'Plasma', gradient: 'linear-gradient(90deg, #0d0887, #7e03a8, #cc4778, #f89540, #f0f921)' },
  { value: 'coolwarm', label: 'CoolWarm', gradient: 'linear-gradient(90deg, #3b4cc0, #7695f3, #c5c9c7, #f2a07b, #b40426)' },
  { value: 'RdYlBu', label: 'RdYlBu', gradient: 'linear-gradient(90deg, #d73027, #fc8d59, #fee090, #91bfdb, #4575b4)' },
  { value: 'hot', label: 'Hot', gradient: 'linear-gradient(90deg, #000000, #e60000, #ffa500, #ffff00, #ffffff)' }
]

// Computed
const numericColumns = computed(() => {
  if (!parsedData.value) return []
  return parsedData.value.columns.filter(c => c.is_numeric)
})

// 判断模板是否支持自动识别数据配对
const isAutoDetectTemplate = computed(() => {
  const name = props.template?.name || ''
  // 这些模板会自动识别数据配对，不需要手动选择列
  const autoTemplates = ['多模型预测效果对比', '模型预测对比', '散点对比']
  return autoTemplates.some(t => name.includes(t))
})

// 检测数据配对（从列名识别 XXX_0/XXX_1 模式）
interface DetectedPair {
  name: string
  x_col: string
  y_col: string
}

const detectedPairs = computed<DetectedPair[]>(() => {
  if (!parsedData.value) return []
  
  const columns = parsedData.value.columns.map(c => c.name)
  const pairs: DetectedPair[] = []
  const pattern01: Record<string, Record<string, string>> = {}
  
  // 匹配 XXX_0 / XXX_1 模式
  for (const col of columns) {
    const match = col.match(/^(.+?)_([01])$/)
    if (match) {
      const [, base, suffix] = match
      if (!pattern01[base]) pattern01[base] = {}
      pattern01[base][suffix] = col
    }
  }
  
  for (const [base, suffixes] of Object.entries(pattern01)) {
    if (suffixes['0'] && suffixes['1']) {
      // 提取模型名（去掉PHIT等前缀）
      let modelName = base
      for (const prefix of ['PHIT', 'PHI', 'PH']) {
        if (modelName.startsWith(prefix)) {
          modelName = modelName.slice(prefix.length)
          break
        }
      }
      modelName = modelName.replace(/_/g, '-') || base
      
      pairs.push({
        name: modelName,
        x_col: suffixes['0'],
        y_col: suffixes['1']
      })
    }
  }
  
  return pairs
})

const canRun = computed(() => {
  // 模型预测对比图、3D曲面图、柱形图、小提琴图/云雨图、子图、三元图、热力图、箱线图、边际组合图等特殊模板只需要有文件
  // 注意：isModelCompareTemplate 需要优先于 isAutoDetectTemplate 检查
  if (isModelCompareTemplate.value || is3DSurfaceTemplate.value || isBarChartTemplate.value || isRaincloudTemplate.value || isSubplotTemplate.value || isTernaryTemplate.value || isGeneralHeatmapTemplate.value || isGeneralBoxplotTemplate.value || isSignificanceBoxplotTemplate.value || isJointPlotTemplate.value) {
    return !!uploadedFile.value
  }
  // 自动识别模板需要有文件且至少选择一个配对
  if (isAutoDetectTemplate.value) {
    return !!uploadedFile.value && chartConfig.value.selected_pairs.length > 0
  }
  return uploadedFile.value && chartConfig.value.y_columns.length > 0
})

// 判断是否是3D曲面图等不需要散点样式的模板
const is3DSurfaceTemplate = computed(() => {
  const name = props.template?.name || ''
  const surfaceTemplates = ['3D曲面图', '热力图', '密度图']
  return surfaceTemplates.some(t => name.includes(t))
})

// 判断是否是柱形图类模板
const isBarChartTemplate = computed(() => {
  const name = props.template?.name || ''
  const barTemplates = ['柱形图', '柱状图', '误差柱', '堆积柱']
  return barTemplates.some(t => name.includes(t))
})

// 判断是否需要显示散点样式选项
const showMarkerOptions = computed(() => {
  return !is3DSurfaceTemplate.value && !isBarChartTemplate.value && !isRaincloudTemplate.value && !isSubplotTemplate.value && !isTernaryTemplate.value && !isModelCompareTemplate.value && !isGeneralHeatmapTemplate.value && !isGeneralBoxplotTemplate.value && !isSignificanceBoxplotTemplate.value && !isJointPlotTemplate.value
})

// 判断是否显示柱形图专属选项
const showBarChartOptions = computed(() => {
  return isBarChartTemplate.value
})

// 判断是否是云雨图/小提琴图类模板
const isRaincloudTemplate = computed(() => {
  const name = props.template?.name || ''
  const raincloudTemplates = ['云雨图', '小提琴图', '提琴图']
  return raincloudTemplates.some(t => name.includes(t))
})

// 判断是否是云雨图（不是普通小提琴图）
const isCloudRainTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('云雨图')
})

// 判断是否是子图/axes模板
const isSubplotTemplate = computed(() => {
  const name = props.template?.name || ''
  const subplotTemplates = ['axes', '子图', 'subplot', '多子图']
  return subplotTemplates.some(t => name.toLowerCase().includes(t.toLowerCase()))
})

// 判断是否是三元图模板
const isTernaryTemplate = computed(() => {
  const name = props.template?.name || ''
  const ternaryTemplates = ['三元', 'ternary', '三相']
  return ternaryTemplates.some(t => name.toLowerCase().includes(t.toLowerCase()))
})

// 判断是否是三元密度图模板
const isTernaryDensityTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('三元密度') || name.includes('ternary density')
})

// 判断是否是热力图模板
const isHeatmapTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('热力图') || name.includes('heatmap')
})

// 判断是否是通用热力图模板（不包括三元密度图）
const isGeneralHeatmapTemplate = computed(() => {
  return isHeatmapTemplate.value && !isTernaryDensityTemplate.value
})

// 判断是否是模型预测对比图模板
const isModelCompareTemplate = computed(() => {
  const name = props.template?.name || ''
  const compareTemplates = ['模型预测对比', '预测对比图', '模型对比']
  return compareTemplates.some(t => name.includes(t))
})

// 判断是否是堆积柱形图模板
const isStackedBarTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('堆积柱') || name.includes('堆积图')
})

// 判断是否是通用柱状图模板
const isGeneralBarTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('通用柱状图') || name.includes('通用柱形图')
})

// 判断是否是误差柱形图模板
const isErrorBarTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('误差柱') || name.includes('分组误差')
})

// 判断是否是相关性散点图模板
const isCorrelationScatterTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('相关性散点') || name.includes('多类别相关')
})

// 判断是否是矩阵气泡图模板
const isMatrixBubbleTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('矩阵气泡') || name.includes('气泡矩阵')
})

// 判断是否是泰勒图模板
const isTaylorTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('泰勒图') || name.toLowerCase().includes('taylor')
})

// 判断是否是显著性标注箱线图模板
const isSignificanceBoxplotTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('显著性') && (name.includes('箱线图') || name.includes('boxplot'))
})

// 判断是否是通用箱线图模板
const isGeneralBoxplotTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('通用箱线图') || (name.includes('箱线图') && !name.includes('显著性'))
})

// 判断是否是边际组合图模板
const isJointPlotTemplate = computed(() => {
  const name = props.template?.name || ''
  return name.includes('边际组合') || name.includes('jointplot') || name.includes('joint plot')
})

// 云雨图样式选项
const raincloudStyles = [
  { value: 1, label: '样式1', desc: '半小提琴 + 箱线图' },
  { value: 2, label: '样式2', desc: '半小提琴 + 统计标记' },
  { value: 3, label: '样式3', desc: '半小提琴 + 散点' },
  { value: 4, label: '样式4', desc: '半小提琴 + 箱线图 + 散点' },
  { value: 5, label: '样式5', desc: '半小提琴 + 箱线图 + 密集散点' },
  { value: 6, label: '样式6', desc: '半小提琴 + 箱线图 + 散点 + 均值连线' }
]

// Methods
function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    processFile(file)
  }
}

function handleDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    processFile(file)
  }
}

async function processFile(file: File) {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['csv', 'xlsx', 'xls'].includes(ext || '')) {
    errorMessage.value = '不支持的文件格式，请上传 .csv, .xlsx 或 .xls 文件'
    return
  }
  
  uploadedFile.value = file
  
  // Parse the file
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const resp = await fetch('/api/templates/parse-data', {
      method: 'POST',
      body: formData
    })
    
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || '解析文件失败')
    }
    
    parsedData.value = await resp.json()
    
    // Auto-select first column as X, numeric columns as Y
    if (parsedData.value && parsedData.value.columns.length > 0) {
      const numCols = parsedData.value.columns.filter(c => c.is_numeric)
      const catCols = parsedData.value.columns.filter(c => !c.is_numeric)
      
      // 小提琴图/云雨图：X轴用分类列，Y轴用数值列
      const templateName = props.template?.name || ''
      const isViolinType = ['云雨图', '小提琴图', '提琴图'].some(t => templateName.includes(t))
      
      if (isViolinType && catCols.length > 0) {
        // 优先选择分类列作为X轴
        chartConfig.value.x_column = catCols[0].name
      } else {
        chartConfig.value.x_column = parsedData.value.columns[0].name
      }
      
      // Auto-select up to 4 numeric columns for Y
      chartConfig.value.y_columns = numCols.slice(0, 4).map(c => c.name)
      
      // Set default title based on file name
      if (!chartConfig.value.title) {
        chartConfig.value.title = file.name.replace(/\.[^.]+$/, '')
      }
      
      // 自动检测并选择所有配对（稍后执行，等待 detectedPairs 计算）
      setTimeout(() => {
        if (detectedPairs.value.length > 0) {
          chartConfig.value.selected_pairs = detectedPairs.value.map(p => p.name)
        }
      }, 100)
    }
  } catch (err: any) {
    errorMessage.value = err.message || '解析文件失败'
    parsedData.value = null
  }
}

function removeFile() {
  uploadedFile.value = null
  parsedData.value = null
  chartConfig.value.x_column = ''
  chartConfig.value.y_columns = []
  chartConfig.value.group_column = ''
  resultImage.value = ''
}

function formatSample(values: any[]): string {
  if (!values || values.length === 0) return ''
  const sample = values.slice(0, 3).map(v => {
    if (typeof v === 'number') return v.toFixed(2)
    return String(v).slice(0, 10)
  }).join(', ')
  return `(${sample}...)`
}

function addColor() {
  chartConfig.value.colors.push('#666666')
}

function removeColor(idx: number) {
  chartConfig.value.colors.splice(idx, 1)
}

function resetConfig() {
  chartConfig.value = { ...defaultConfig }
  if (parsedData.value && parsedData.value.columns.length > 0) {
    chartConfig.value.x_column = parsedData.value.columns[0].name
    const numCols = parsedData.value.columns.filter(c => c.is_numeric)
    chartConfig.value.y_columns = numCols.slice(0, 4).map(c => c.name)
  }
}

async function runChart() {
  if (!props.template || !uploadedFile.value || !canRun.value) return
  
  isRunning.value = true
  errorMessage.value = ''
  resultImage.value = ''
  
  try {
    const formData = new FormData()
    formData.append('template_id', props.template.id)
    formData.append('config', JSON.stringify(chartConfig.value))
    formData.append('files', uploadedFile.value)
    
    const resp = await fetch('/api/templates/run-configured', {
      method: 'POST',
      body: formData
    })
    
    if (!resp.ok) {
      const err = await resp.json()
      throw new Error(err.detail || '生成图表失败')
    }
    
    const blob = await resp.blob()
    resultImage.value = URL.createObjectURL(blob)
  } catch (err: any) {
    errorMessage.value = err.message || '生成图表失败'
  } finally {
    isRunning.value = false
  }
}

function downloadImage() {
  if (!resultImage.value) return
  
  const a = document.createElement('a')
  a.href = resultImage.value
  a.download = `${props.template?.name || 'chart'}_${Date.now()}.png`
  a.click()
}

function zoomIn() {
  zoomLevel.value = Math.min(zoomLevel.value + 0.25, 3)
}

function zoomOut() {
  zoomLevel.value = Math.max(zoomLevel.value - 0.25, 0.25)
}

function resetZoom() {
  zoomLevel.value = 1
}
</script>

<style scoped>
.chart-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f6fa;
  overflow: hidden;
}

/* Header */
.editor-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #374151;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.template-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.template-name {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.category-badge {
  padding: 4px 10px;
  background: #dbeafe;
  color: #1d4ed8;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn-primary, .btn-secondary {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Body Layout */
.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

/* Config Panel */
.config-panel {
  width: 360px;
  background: white;
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
  padding: 16px;
}

.config-section {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f3f4f6;
}

.config-section:last-child {
  border-bottom: none;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
}

.step-num {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.collapsed-title {
  cursor: pointer;
  user-select: none;
}

.collapsed-title:hover {
  color: #4f46e5;
}

.collapse-icon {
  font-size: 10px;
  color: #6b7280;
}

/* Upload Zone */
.upload-zone {
  border: 2px dashed #d1d5db;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-zone:hover, .upload-zone.drag-over {
  border-color: #4f46e5;
  background: #f5f3ff;
}

.upload-zone.has-file {
  border-style: solid;
  border-color: #10b981;
  background: #ecfdf5;
  cursor: default;
}

.upload-icon {
  font-size: 36px;
  display: block;
  margin-bottom: 8px;
}

.upload-text {
  display: block;
  color: #374151;
  font-size: 14px;
  margin-bottom: 4px;
}

.upload-hint {
  display: block;
  color: #9ca3af;
  font-size: 12px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
}

.file-icon {
  font-size: 28px;
}

.file-details {
  flex: 1;
}

.file-name {
  display: block;
  font-weight: 500;
  color: #111827;
  font-size: 14px;
}

.file-meta {
  display: block;
  color: #6b7280;
  font-size: 12px;
}

.remove-file {
  width: 24px;
  height: 24px;
  border: none;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
}

.remove-file:hover {
  background: #fecaca;
}

/* Form Elements */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.form-group.half {
  flex: 1;
}

.form-group.third {
  flex: 1;
  min-width: 0;
}

.form-select, .form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  background: white;
  color: #111827;
  transition: border-color 0.2s;
}

.form-select:focus, .form-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.form-range {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #e5e7eb;
  border-radius: 3px;
  outline: none;
}

.form-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  background: #4f46e5;
  border-radius: 50%;
  cursor: pointer;
}

.range-value {
  display: block;
  text-align: right;
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

/* Column Picker */
.column-picker {
  max-height: 180px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.column-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f3f4f6;
}

.column-option:last-child {
  border-bottom: none;
}

.column-option:hover {
  background: #f9fafb;
}

.column-option.selected {
  background: #ede9fe;
}

.column-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #4f46e5;
}

.col-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #111827;
}

.col-sample {
  font-size: 11px;
  color: #9ca3af;
}

/* Marker Picker */
.marker-picker {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.marker-btn {
  width: 36px;
  height: 36px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  background: white;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.15s;
}

.marker-btn:hover {
  border-color: #a5b4fc;
}

.marker-btn.active {
  border-color: #4f46e5;
  background: #ede9fe;
}

/* Colormap Picker */
.colormap-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.colormap-btn {
  width: 48px;
  height: 24px;
  border: 2px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.colormap-btn:hover {
  transform: scale(1.1);
}

.colormap-btn.active {
  border-color: #111827;
  box-shadow: 0 0 0 2px white, 0 0 0 4px #4f46e5;
}

/* Raincloud Style Picker */
.raincloud-style-picker {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.style-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.style-option:hover {
  border-color: #a5b4fc;
  background: #f5f3ff;
}

.style-option.selected {
  border-color: #4f46e5;
  background: #ede9fe;
}

.style-num {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #4f46e5;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.style-option.selected .style-num {
  background: #3730a3;
}

.style-desc {
  font-size: 13px;
  color: #374151;
}

/* Color List */
.color-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.color-item {
  position: relative;
}

.color-input {
  width: 36px;
  height: 36px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  padding: 2px;
}

.remove-color {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  border: none;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  font-size: 10px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
}

.color-item:hover .remove-color {
  opacity: 1;
}

.add-color {
  padding: 8px 12px;
  border: 1px dashed #d1d5db;
  border-radius: 8px;
  background: transparent;
  color: #6b7280;
  font-size: 12px;
  cursor: pointer;
}

.add-color:hover {
  border-color: #4f46e5;
  color: #4f46e5;
}

/* Checkboxes */
.checkboxes {
  margin-top: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #4f46e5;
}

/* Data Preview */
.data-preview {
  margin-top: 12px;
  overflow-x: auto;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.preview-table th, .preview-table td {
  padding: 6px 8px;
  border: 1px solid #e5e7eb;
  text-align: left;
  white-space: nowrap;
}

.preview-table th {
  background: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.preview-table td {
  color: #6b7280;
}

/* Preview Panel */
.preview-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f6fa;
  overflow: hidden;
  min-height: 0;
}

.preview-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.preview-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.toolbar-btn {
  padding: 8px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.toolbar-btn:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.zoom-level {
  margin-left: auto;
  font-size: 13px;
  color: #6b7280;
}

.preview-scroll {
  flex: 1;
  overflow: auto;
  padding: 20px;
  min-height: 0;
}

.result-image {
  display: block;
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform-origin: top center;
  transition: transform 0.2s;
  margin: 0 auto;
}

/* Placeholder */
.preview-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-content {
  text-align: center;
  color: #9ca3af;
}

.placeholder-icon {
  font-size: 64px;
  display: block;
  margin-bottom: 16px;
  opacity: 0.5;
}

.placeholder-content h3 {
  font-size: 18px;
  color: #6b7280;
  margin-bottom: 8px;
}

.placeholder-content p {
  font-size: 14px;
}

/* Loading */
.loading-animation {
  text-align: center;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

.loading-animation p {
  color: #6b7280;
  font-size: 14px;
}

/* Error Display */
.error-display {
  text-align: center;
  max-width: 600px;
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.error-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}

.error-display h3 {
  font-size: 18px;
  color: #dc2626;
  margin-bottom: 12px;
}

.error-message {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 12px;
  font-size: 12px;
  color: #991b1b;
  text-align: left;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  margin-bottom: 16px;
}

/* Auto Detect Info */
.auto-detect-info {
  background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
  border: 1px solid #86efac;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}

.auto-detect-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.auto-detect-text strong {
  display: block;
  color: #166534;
  font-size: 14px;
  margin-bottom: 4px;
}

.auto-detect-text p {
  color: #4ade80;
  font-size: 12px;
  margin: 0;
}

.detected-pairs {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pair-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: white;
  border: 1px solid #d1fae5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.pair-option:hover {
  border-color: #34d399;
  background: #f0fdf4;
}

.pair-option.selected {
  border-color: #10b981;
  background: #d1fae5;
}

.pair-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #10b981;
}

.pair-name {
  font-weight: 600;
  color: #166534;
  font-size: 13px;
}

.pair-cols {
  flex: 1;
  text-align: right;
  font-size: 11px;
  color: #6b7280;
  font-family: monospace;
}

.pair-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #6b7280;
  text-align: center;
}

.detected-columns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
  justify-content: center;
}

.column-tag {
  padding: 4px 10px;
  background: white;
  border: 1px solid #86efac;
  border-radius: 4px;
  font-size: 11px;
  color: #166534;
  font-family: monospace;
}
</style>

