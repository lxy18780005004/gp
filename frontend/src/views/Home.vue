<template>
  <div class="kline-page">
    <!-- 查询表单 -->
    <el-card class="query-card">
      <div class="query-section">
        <div class="input-row">
          <div>
            <el-input
              v-model="queryForm.ts_code"
              placeholder="输入股票代码，多个代码用逗号分隔，例如：000001.SZ,600000.SH"
              clearable
              class="code-input"
            >
              <template #prepend>股票代码</template>
            </el-input>
          </div>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYYMMDD"
          />

          <el-button
            type="primary"
            @click="fetchKlineData"
            :loading="loading"
          >
            <el-icon><Search /></el-icon>
            查询K线
          </el-button>

          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleFileChange"
            accept=".xlsx,.xls"
          >
            <el-button type="success">
              <el-icon><Upload /></el-icon>
              导入Excel
            </el-button>
          </el-upload>
        </div>

        <div class="action-row">
          <div class="left-actions">
            <el-radio-group v-model="queryForm.freq" @change="handleFreqChange">
              <el-radio-button label="D">日线</el-radio-button>
              <el-radio-button label="W">周线</el-radio-button>
              <el-radio-button label="M">月线</el-radio-button>
            </el-radio-group>

            <el-divider direction="vertical" />

            <el-button-group>
              <el-button @click="setAllChartsZoom(0, 100)" size="small">
                <el-icon><FullScreen /></el-icon>
                全部显示
              </el-button>
              <el-button @click="setAllChartsZoom(70, 100)" size="small">
                <el-icon><ZoomIn /></el-icon>
                最近30%
              </el-button>
              <el-button @click="setAllChartsZoom(50, 100)" size="small">
                <el-icon><ZoomIn /></el-icon>
                最近50%
              </el-button>
            </el-button-group>
            
            <el-divider direction="vertical" />
            
            <span class="legend-control-label">均线：</span>
            <el-button-group size="small">
              <el-button 
                :type="globalLegendState.MA5 ? 'primary' : ''"
                @click="toggleAllSeries('MA5')"
              >
                MA5
              </el-button>
              <el-button 
                :type="globalLegendState.MA10 ? 'primary' : ''"
                @click="toggleAllSeries('MA10')"
              >
                MA10
              </el-button>
              <el-button 
                :type="globalLegendState.MA20 ? 'primary' : ''"
                @click="toggleAllSeries('MA20')"
              >
                MA20
              </el-button>
              <el-button 
                :type="globalLegendState.MA30 ? 'primary' : ''"
                @click="toggleAllSeries('MA30')"
              >
                MA30
              </el-button>
            </el-button-group>

            <el-divider direction="vertical" />

            <el-button
              @click="clearCharts"
            >
              <el-icon><Delete /></el-icon>
              清空
            </el-button>

            <span v-if="chartList.length > 0" class="stock-count">
              已加载 {{ chartList.length }} 个股票
            </span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- K线图表网格 -->
    <div class="charts-grid" v-loading="loading">
      <el-card
        v-for="(chart, index) in chartList"
        :key="chart.ts_code"
        class="chart-card"
        :body-style="{ padding: '10px' }"
      >
        <template #header>
          <div class="chart-header">
            <div class="stock-title">
              <span class="stock-name">{{ chart.name }}</span>
              <span class="stock-code">{{ chart.ts_code }}</span>
              <span class="legend-items">
                <span
                  class="legend-item clickable"
                  :class="{ active: !chart.hiddenSeries || !chart.hiddenSeries.includes('K线') }"
                  @click="toggleSeries(index, 'K线')"
                >
                  K线
                </span>
                <span
                  class="legend-item ma5 clickable"
                  :class="{ active: !chart.hiddenSeries || !chart.hiddenSeries.includes('MA5') }"
                  @click="toggleSeries(index, 'MA5')"
                >
                  MA5
                </span>
                <span
                  class="legend-item ma10 clickable"
                  :class="{ active: !chart.hiddenSeries || !chart.hiddenSeries.includes('MA10') }"
                  @click="toggleSeries(index, 'MA10')"
                >
                  MA10
                </span>
                <span
                  class="legend-item ma20 clickable"
                  :class="{ active: !chart.hiddenSeries || !chart.hiddenSeries.includes('MA20') }"
                  @click="toggleSeries(index, 'MA20')"
                >
                  MA20
                </span>
                <span
                  class="legend-item ma30 clickable"
                  :class="{ active: !chart.hiddenSeries || !chart.hiddenSeries.includes('MA30') }"
                  @click="toggleSeries(index, 'MA30')"
                >
                  MA30
                </span>
              </span>
            </div>
            <div class="stock-stats">
              <el-tooltip
                v-if="chart.hoverInfo"
                :content="`从 ${chart.hoverInfo.date} 至今累计涨幅: ${chart.hoverInfo.totalChange >= 0 ? '+' : ''}${chart.hoverInfo.totalChange}%`"
                placement="top"
              >
                <span :class="['hover-change', chart.hoverInfo.totalChange >= 0 ? 'positive' : 'negative']">
                  至今{{ chart.hoverInfo.totalChange >= 0 ? '+' : '' }}{{ chart.hoverInfo.totalChange }}%
                </span>
              </el-tooltip>
              <span class="price">{{ chart.info.latest_price }}</span>
              <span :class="['change', chart.info.change_pct >= 0 ? 'positive' : 'negative']">
                {{ chart.info.change_pct >= 0 ? '+' : '' }}{{ chart.info.change_pct.toFixed(2) }}%
              </span>
            </div>
          </div>
        </template>
        <div :ref="el => setChartRef(el, index)" class="chart-container"></div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="chartList.length === 0 && !loading"
      description="请输入股票代码或导入Excel文件查询K线数据"
      :image-size="150"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { Search, Upload, Delete, FullScreen, ZoomIn } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import axios from 'axios'
import * as XLSX from 'xlsx'

const API_BASE_URL = 'http://localhost:5000'

const queryForm = ref({
  ts_code: '000001.SZ',
  freq: 'D',
  start_date: '20250101',
  end_date: '20260128'
})

const dateRange = ref(['20250101', '20260128'])

const loading = ref(false)
const uploadRef = ref(null)
const chartList = ref([])
const chartRefs = ref([])
const chartInstances = []

// 全局图例状态
const globalLegendState = ref({
  MA5: true,
  MA10: true,
  MA20: true,
  MA30: true
})

// 监听日期范围变化
const updateDateRange = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    queryForm.value.start_date = dateRange.value[0]
    queryForm.value.end_date = dateRange.value[1]
  }
}

// 周期切换处理
const handleFreqChange = () => {
  if (chartList.value.length > 0) {
    fetchKlineData()
  }
}

// 统一设置所有图表的缩放
const setAllChartsZoom = (start, end) => {
  if (chartInstances.length === 0) {
    ElMessage.warning('请先查询股票数据')
    return
  }

  chartInstances.forEach(instance => {
    if (instance) {
      instance.dispatchAction({
        type: 'dataZoom',
        start: start,
        end: end
      })
    }
  })

  const zoomText = start === 0 ? '100%' : `${end - start}%`
}

// 切换系列显示/隐藏
const toggleSeries = (chartIndex, seriesName) => {
  const chart = chartList.value[chartIndex]
  if (!chart) return

  // 初始化隐藏系列数组
  if (!chart.hiddenSeries) {
    chart.hiddenSeries = []
  }

  // 切换系列状态
  const index = chart.hiddenSeries.indexOf(seriesName)
  if (index > -1) {
    chart.hiddenSeries.splice(index, 1)
  } else {
    chart.hiddenSeries.push(seriesName)
  }

  // 获取对应的图表实例
  const chartInstance = chartInstances[chartIndex]
  if (chartInstance) {
    // 使用 ECharts 的 legendToggleSelect 动作
    chartInstance.dispatchAction({
      type: 'legendToggleSelect',
      name: seriesName
    })
  }
}

// 统一切换所有图表的某个系列
const toggleAllSeries = (seriesName) => {
  if (chartInstances.length === 0) {
    ElMessage.warning('请先查询股票数据')
    return
  }
  
  // 切换全局状态
  globalLegendState.value[seriesName] = !globalLegendState.value[seriesName]
  const isShow = globalLegendState.value[seriesName]
  
  // 应用到所有图表
  chartList.value.forEach((chart, index) => {
    if (!chart.hiddenSeries) {
      chart.hiddenSeries = []
    }
    
    const hiddenIndex = chart.hiddenSeries.indexOf(seriesName)
    
    if (isShow && hiddenIndex > -1) {
      // 需要显示，但当前是隐藏的
      chart.hiddenSeries.splice(hiddenIndex, 1)
      chartInstances[index]?.dispatchAction({
        type: 'legendToggleSelect',
        name: seriesName
      })
    } else if (!isShow && hiddenIndex === -1) {
      // 需要隐藏，但当前是显示的
      chart.hiddenSeries.push(seriesName)
      chartInstances[index]?.dispatchAction({
        type: 'legendToggleSelect',
        name: seriesName
      })
    }
  })
  
}

// 设置图表引用
const setChartRef = (el, index) => {
  if (el) {
    chartRefs.value[index] = el
  }
}

// 初始化单个图表
const initChart = (container) => {
  if (container) {
    return echarts.init(container)
  }
  return null
}

// 处理K线数据
const processKlineData = (data) => {
  const categoryData = []
  const values = []
  const volumes = []

  data.forEach(item => {
    categoryData.push(item.date)
    values.push([item.open, item.close, item.low, item.high])
    volumes.push([categoryData.length - 1, item.vol, item.change > 0 ? 1 : -1])
  })

  return { categoryData, values, volumes }
}

// 计算移动平均线
const calculateMA = (data, dayCount) => {
  const result = []
  for (let i = 0; i < data.length; i++) {
    if (i < dayCount) {
      result.push('-')
      continue
    }
    let sum = 0
    for (let j = 0; j < dayCount; j++) {
      sum += data[i - j][1]
    }
    result.push((sum / dayCount).toFixed(2))
  }
  return result
}

// 渲染单个图表
const renderChart = (chartInstance, klineData, stockName) => {
  const { categoryData, values, volumes } = processKlineData(klineData)

  const upColor = '#ec0000'
  const startColor = '#188ffe'
  const endColor = '#ec00a7'
  const upBorderColor = '#8A0000'
  const downColor = '#00da3c'
  const downBorderColor = '#008F28'

  // 找到对应的图表数据对象
  const chartData = chartList.value.find(c => c.name === stockName)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: function(params) {
        let result = params[0].name + '<br/>'

        // 找到K线数据
        let klineParam = params.find(p => p.seriesName === 'K线')
        if (klineParam) {
          const open = klineParam.data[1]
          const close = klineParam.data[2]
          const low = klineParam.data[3]
          const high = klineParam.data[4]

          // 计算涨跌幅
          const change = close - open
          const changePct = open !== 0 ? ((change / open) * 100).toFixed(2) : 0
          const changeColor = change >= 0 ? upColor : downColor
          const changeSymbol = change >= 0 ? '+' : ''

          // 计算从鼠标悬停日期（开盘价）到当前日期（最后一天收盘价）的累计涨幅
          if (chartData && values.length > 0) {
            const lastClose = values[values.length - 1][1] // 最后一天的收盘价
            const totalChange = open !== 0 ? (((lastClose - open) / open) * 100).toFixed(2) : 0

            // 更新图表的悬停信息
            chartData.hoverInfo = {
              date: params[0].name,
              totalChange: totalChange
            }
          }

          // 涨跌信息显示在顶部
          result += `<span style="color: ${changeColor}; font-weight: bold; font-size: 14px;">涨跌额: ${changeSymbol}${change.toFixed(2)}</span><br/>`
          result += `<span style="color: ${changeColor}; font-weight: bold; font-size: 14px;">涨跌幅: ${changeSymbol}${changePct}%</span><br/>`

          // 价格信息（开盘和收盘带颜色）
          result += `开盘: <span style="color: ${startColor}; font-weight: bold;">${open}</span><br/>`
          result += `收盘: <span style="color: ${endColor}; font-weight: bold;">${close}</span><br/>`
          result += `最低: ${low}<br/>`
          result += `最高: ${high}<br/>`
        }

        // 显示成交量
        let volumeParam = params.find(p => p.seriesName === '成交量')
        if (volumeParam) {
          result += `成交量: ${(volumeParam.data[1] / 10000).toFixed(2)}万手<br/>`
        }

        return result
      }
    },
    legend: {
      show: false,
      selected: {
        'K线': true,
        'MA5': true,
        'MA10': true,
        'MA20': true,
        'MA30': true
      }
    },
    grid: [
      {
        left: '8%',
        right: '5%',
        top: '8%',
        height: '62%'
      },
      {
        left: '8%',
        right: '5%',
        top: '75%',
        height: '15%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: categoryData,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        axisLabel: { fontSize: 10 },
        min: 'dataMin',
        max: 'dataMax'
      },
      {
        type: 'category',
        gridIndex: 1,
        data: categoryData,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }
    ],
    yAxis: [
      {
        scale: true,
        axisLabel: { fontSize: 10 },
        splitArea: {
          show: true
        }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 70,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        top: '93%',
        height: 15,
        start: 70,
        end: 100
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: values,
        itemStyle: {
          color: upColor,
          color0: downColor,
          borderColor: upBorderColor,
          borderColor0: downBorderColor
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: calculateMA(values, 5),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          color: '#c23531',
          opacity: 0.8,
          width: 1.5
        }
      },
      {
        name: 'MA10',
        type: 'line',
        data: calculateMA(values, 10),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          color: '#4c82af',
          opacity: 0.8,
          width: 1.5
        }
      },
      {
        name: 'MA20',
        type: 'line',
        data: calculateMA(values, 20),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          color: '#ffba00',
          opacity: 0.8,
          width: 1.5
        }
      },
      {
        name: 'MA30',
        type: 'line',
        data: calculateMA(values, 30),
        smooth: true,
        showSymbol: false,
        lineStyle: {
          color: '#ff641f',
          opacity: 0.8,
          width: 1.5
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: function(params) {
            return params.data[2] > 0 ? upColor : downColor
          }
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

// 获取单个股票K线数据
const fetchSingleKlineData = async (ts_code) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/stock/kline`, {
      params: {
        ts_code,
        freq: queryForm.value.freq,
        start_date: queryForm.value.start_date,
        end_date: queryForm.value.end_date
      }
    })

    if (response.data.code === 0) {
      const { data, name, info } = response.data

      if (data.length === 0) {
        return null
      }

      return {
        ts_code,
        name,
        data,
        info,
        hoverInfo: null,
        hiddenSeries: []
      }
    }
  } catch (error) {
    console.error(`查询 ${ts_code} 失败:`, error)
  }
  return null
}

// 批量获取K线数据
const fetchKlineData = async () => {
  if (!queryForm.value.ts_code) {
    ElMessage.warning('请输入股票代码')
    return
  }

  // 更新日期范围
  updateDateRange()

  // 清空之前的图表
  clearCharts()

  // 分割股票代码
  const codes = queryForm.value.ts_code.split(/[,，\s]+/).filter(code => code.trim())

  if (codes.length === 0) {
    ElMessage.warning('请输入有效的股票代码')
    return
  }

  loading.value = true

  try {
    // 并发请求所有股票数据
    const promises = codes.map(code => fetchSingleKlineData(code.trim()))
    const results = await Promise.all(promises)

    // 过滤掉失败的请求
    const validResults = results.filter(result => result !== null)

    if (validResults.length === 0) {
      ElMessage.warning('未查询到任何数据')
      return
    }

    chartList.value = validResults

    // 等待DOM更新后渲染图表
    await nextTick()
    renderAllCharts()

    ElMessage.success(`成功加载 ${validResults.length} 个股票`)
  } catch (error) {
    console.error('批量查询失败:', error)
    ElMessage.error('查询失败，请检查后端服务是否启动')
  } finally {
    loading.value = false
  }
}

// 渲染所有图表
const renderAllCharts = () => {
  // 清理旧的图表实例
  chartInstances.forEach(instance => {
    if (instance) {
      instance.dispose()
    }
  })
  chartInstances.length = 0

  // 创建新的图表实例并渲染
  chartList.value.forEach((chart, index) => {
    const container = chartRefs.value[index]
    if (container) {
      const instance = initChart(container)
      if (instance) {
        chartInstances.push(instance)
        renderChart(instance, chart.data, chart.name)
      }
    }
  })
}

// 处理Excel文件上传
const handleFileChange = (file) => {
  const reader = new FileReader()

  reader.onload = async (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })

      // 读取第一个sheet
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
      const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 })

      // 提取股票代码（假设在第一列）
      const codes = []
      for (let i = 0; i < jsonData.length; i++) {
        const code = jsonData[i][0]
        if (code && typeof code === 'string' && code.trim()) {
          codes.push(code.trim())
        }
      }

      if (codes.length === 0) {
        ElMessage.warning('Excel文件中未找到股票代码')
        return
      }

      // 设置到查询表单并执行查询
      queryForm.value.ts_code = codes.join(',')
      await fetchKlineData()

    } catch (error) {
      console.error('Excel解析失败:', error)
      ElMessage.error('Excel文件解析失败')
    }
  }

  reader.readAsArrayBuffer(file.raw)
}

// 清空所有图表
const clearCharts = () => {
  chartInstances.forEach(instance => {
    if (instance) {
      instance.dispose()
    }
  })
  chartInstances.length = 0
  chartList.value = []
  chartRefs.value = []
}

// 窗口大小改变时重新调整图表
const handleResize = () => {
  chartInstances.forEach(instance => {
    if (instance) {
      instance.resize()
    }
  })
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  clearCharts()
})
</script>

<style scoped>
.kline-page {
  padding: 15px;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.query-card {
  flex-shrink: 0;
}

.query-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.input-row {
  gap: 10px;
}

.input-row > * {
  display: inline-block;
  vertical-align: middle;
  margin-right: 10px;
}

.code-input {
  width: 300px;
  flex-shrink: 0;
  flex-grow: 0;
}

.date-picker {
  width: 100px !important;
  min-width: 100px !important;
  max-width: 100px !important;
}

.action-row {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 15px;
  margin-top: 10px;
}

.left-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
  flex: 1;
}

.stock-count {
  color: #67C23A;
  font-size: 14px;
  font-weight: 500;
  margin-left: 5px;
}

.el-divider--vertical {
  height: 1.5em;
  margin: 0 8px;
}

.legend-control-label {
  font-size: 14px;
  color: #606266;
  margin-right: 5px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  flex: 1;
  overflow-y: auto;
  align-items: start;
  grid-auto-rows: min-content;
}

.chart-card {
  height: fit-content;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
}

.stock-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stock-name {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.stock-code {
  font-size: 12px;
  color: #909399;
}

.hover-change {
  font-size: 12px;
  font-weight: bold;
  margin-left: 8px;
  cursor: help;
}

.legend-items {
  display: inline-flex;
  gap: 8px;
  margin-left: 12px;
  font-size: 11px;
}

.legend-item {
  color: #606266;
  white-space: nowrap;
}

.legend-item.clickable {
  cursor: pointer;
  user-select: none;
  transition: opacity 0.3s;
}

.legend-item.clickable:hover {
  opacity: 0.7;
}

.legend-item.clickable:not(.active) {
  opacity: 0.3;
  text-decoration: line-through;
}

.legend-item.ma5 {
  color: #c23531;
}

.legend-item.ma10 {
  color: #4c82af;
}

.legend-item.ma20 {
  color: #ffba00;
}

.legend-item.ma30 {
  color: #ff641f;
}

.stock-stats {
  display: flex;
  align-items: center;
  gap: 10px;
}

.price {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.change {
  font-size: 14px;
  font-weight: bold;
}

.positive {
  color: #ec0000;
}

.negative {
  color: #00da3c;
}

.chart-container {
  width: 100%;
  height: 400px;
}

/* 响应式布局 */
@media (max-width: 1400px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
