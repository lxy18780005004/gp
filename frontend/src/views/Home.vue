<template>
  <div class="home">
    <header class="header">
      <div>
        <h1>欢迎使用 Tushare 数据平台</h1>
        <p>实时获取金融市场数据</p>
      </div>
      <div class="status-group">
        <div class="status">
          <span :class="['status-dot', backendStatus ? 'online' : 'offline']"></span>
          <span class="status-text">{{ backendStatus ? '服务在线' : '服务离线' }}</span>
        </div>
        <div class="status">
          <span :class="['status-dot', redisStatus === 'connected' ? 'online' : 'offline']"></span>
          <span class="status-text">Redis {{ redisStatus === 'connected' ? '已连接' : '未连接' }}</span>
        </div>
      </div>
    </header>

    <div class="content">
      <div class="card">
        <h3>K线图查询</h3>
        
        <QueryForm 
          :query="query"
          :loading="loading"
          :imported-count="importedStocks.length"
          :show-zoom-controls="displayedStocks.length > 0"
          @update:query="query = $event"
          @file-upload="handleFileUpload"
          @clear-import="clearImport"
          @query="fetchKlineData"
          @zoom-all="zoomAll"
          ref="queryFormRef"
        />

        <el-alert
          v-if="error"
          :title="error"
          type="error"
          :closable="false"
          style="margin-bottom: 12px;"
        />

        <div class="charts-container" :style="{ gridTemplateColumns: getGridColumns() }">
          <!-- 股票图表 -->
          <div 
            v-for="(stock, index) in displayedStocks"
            :key="stock.code + '_' + index"
            class="stock-chart-container"
          >
            <!-- 股票信息头部 -->
            <div class="stock-info-header">
              <div class="stock-title-row">
                <span class="stock-name">{{ stock.name }}</span>
                <span class="stock-code">{{ stock.code }}</span>
                <span 
                  v-if="stock.currentChange !== null" 
                  :class="['change-badge', stock.currentChange >= 0 ? 'positive' : 'negative']"
                >
                  {{ stock.currentChange >= 0 ? '+' : '' }}{{ stock.currentChange.toFixed(2) }}%
                </span>
              </div>
              
              <div class="stock-metrics-row">
                <div class="metric-item">
                  <span class="metric-label">最新</span>
                  <span class="metric-value">{{ stock.info.latest_price }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">涨跌</span>
                  <span :class="['metric-value', stock.info.change >= 0 ? 'positive' : 'negative']">
                    {{ stock.info.change >= 0 ? '+' : '' }}{{ stock.info.change }}
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">幅度</span>
                  <span :class="['metric-value', stock.info.change_pct >= 0 ? 'positive' : 'negative']">
                    {{ stock.info.change_pct >= 0 ? '+' : '' }}{{ stock.info.change_pct }}%
                  </span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">最高</span>
                  <span class="metric-value">{{ stock.info.high }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">最低</span>
                  <span class="metric-value">{{ stock.info.low }}</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">成交量</span>
                  <span class="metric-value">{{ formatNumber(stock.info.volume) }}</span>
                </div>
              </div>
            </div>

            <!-- 图表容器 -->
            <div :ref="el => setChartRef(el, index)" class="chart-container"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import QueryForm from '../components/QueryForm.vue'

// 计算默认日期范围
const getDefaultDates = (freq = 'D') => {
  const endDate = new Date()
  const startDate = new Date()
  
  if (freq === 'D') {
    startDate.setDate(startDate.getDate() - 15)
  } else if (freq === 'W') {
    startDate.setFullYear(startDate.getFullYear() - 1)
  } else if (freq === 'M') {
    startDate.setFullYear(startDate.getFullYear() - 5)
  }
  
  const formatDate = (date) => {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }
  
  return {
    start: formatDate(startDate),
    end: formatDate(endDate)
  }
}

const backendStatus = ref(false)
const redisStatus = ref('unknown')
const loading = ref(false)
const error = ref('')
const queryFormRef = ref(null)

// 图表实例数组
const chartInstances = ref([])
const chartContainers = ref([])

// 存储导入的股票代码
const importedStocks = ref([])

// 显示的股票数据
const displayedStocks = ref([])

// 存储每个股票的完整数据
const stocksFullData = ref([])

const defaultDates = getDefaultDates('D')

const query = ref({
  stock1: '603061.SH',
  startDate: defaultDates.start,
  endDate: defaultDates.end,
  freq: 'D'
})

// 工具函数：格式化数字
const formatNumber = (num) => {
  if (!num) return '0'
  const absNum = Math.abs(num)
  if (absNum >= 100000000) return (absNum / 100000000).toFixed(2) + '亿'
  if (absNum >= 10000) return (absNum / 10000).toFixed(2) + '万'
  return absNum.toFixed(2)
}

// 工具函数：格式化日期
const formatDate = (dateStr, freq) => {
  if (!dateStr) return ''
  const year = dateStr.substring(0, 4)
  const month = dateStr.substring(4, 6)
  const day = dateStr.substring(6, 8)
  
  if (freq === 'M') return `${year}年${month}月`
  if (freq === 'W') return `${month}月${day}日`
  return `${month}月${day}日`
}

// 设置图表容器引用
const setChartRef = (el, index) => {
  if (el) {
    chartContainers.value[index] = el
  }
}

// 初始化单个图表
const initChart = (index) => {
  const container = chartContainers.value[index]
  if (!container) return
  
  // 销毁旧实例
  if (chartInstances.value[index]) {
    chartInstances.value[index].dispose()
  }
  
  // 创建新实例
  const chartInstance = echarts.init(container)
  chartInstances.value[index] = chartInstance
  
  const stock = displayedStocks.value[index]
  const stockData = stocksFullData.value[index] || []
  
  // 基础配置
  const option = {
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        crossStyle: {
          color: '#999'
        },
        lineStyle: {
          color: '#999',
          type: 'dashed'
        }
      },
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#d0d0d0',
      borderWidth: 1,
      padding: 12,
      textStyle: {
        color: '#2c3e50',
        fontSize: 12
      },
      formatter: (params) => {
        if (!params || params.length === 0) return ''
        
        const dataIndex = params[0].dataIndex
        if (!stockData || dataIndex >= stockData.length) return ''
        
        const item = stockData[dataIndex]
        const dateLabel = formatDate(item.date, query.value.freq)
        
        const change = item.change || 0
        const changePct = item.change_pct || 0
        const changeColor = change >= 0 ? '#ef232a' : '#14b143'
        const changeSign = change >= 0 ? '+' : ''
        
        const moneyFlow = item.money_flow || 0
        const moneyFlowColor = moneyFlow >= 0 ? '#ef232a' : '#14b143'
        const moneyFlowLabel = moneyFlow >= 0 ? '流入' : '流出'
        
        return `
          <div style="font-weight: 600; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #e8e8e8;">
            ${dateLabel}
          </div>
          <div style="display: grid; grid-template-columns: auto 1fr; gap: 6px 12px;">
            <span style="color: #7f8c8d;">涨跌</span>
            <span style="color: ${changeColor}; font-weight: 500; text-align: right;">
              ${changeSign}${change} (${changeSign}${changePct}%)
            </span>
            
            <span style="color: #7f8c8d;">资金</span>
            <span style="color: ${moneyFlowColor}; font-weight: 500; text-align: right;">
              ${moneyFlowLabel} ${formatNumber(Math.abs(moneyFlow))}
            </span>
            
            <span style="color: #7f8c8d;">开盘</span>
            <span style="font-weight: 500; text-align: right;">${item.open}</span>
            
            <span style="color: #7f8c8d;">收盘</span>
            <span style="font-weight: 500; text-align: right;">${item.close}</span>
            
            <span style="color: #7f8c8d;">最高</span>
            <span style="font-weight: 500; text-align: right;">${item.high}</span>
            
            <span style="color: #7f8c8d;">最低</span>
            <span style="font-weight: 500; text-align: right;">${item.low}</span>
            
            <span style="color: #7f8c8d;">成交量</span>
            <span style="font-weight: 500; text-align: right;">${formatNumber(item.vol || 0)}</span>
            
            <span style="color: #7f8c8d;">成交额</span>
            <span style="font-weight: 500; text-align: right;">${formatNumber(item.amount || 0)}</span>
          </div>
        `
      }
    },
    grid: [
      {
        left: '4%',
        right: '2%',
        top: '2%',
        height: '62%',
        containLabel: false
      },
      {
        left: '4%',
        right: '2%',
        top: '68%',
        height: '22%',
        containLabel: false
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: [],
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#ddd' } },
        axisLabel: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      },
      {
        type: 'category',
        gridIndex: 1,
        data: [],
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#ddd' } },
        axisLabel: { 
          color: '#666',
          fontSize: 11
        },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    yAxis: [
      {
        type: 'value',
        scale: true,
        splitLine: { 
          lineStyle: { color: '#f0f0f0' }
        },
        axisLabel: { 
          color: '#666',
          fontSize: 11
        }
      },
      {
        type: 'value',
        gridIndex: 1,
        scale: true,
        splitNumber: 2,
        splitLine: { show: false },
        axisLabel: { 
          color: '#666',
          fontSize: 11,
          formatter: (value) => {
            if (value >= 100000000) return (value / 100000000).toFixed(0) + '亿'
            if (value >= 10000) return (value / 10000).toFixed(0) + '万'
            return value.toFixed(0)
          }
        }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100,
        height: 8,
        bottom: 0,
        borderColor: 'transparent',
        backgroundColor: '#f5f5f5',
        fillerColor: 'rgba(52, 152, 219, 0.2)',
        handleStyle: {
          color: '#3498db'
        },
        textStyle: {
          color: '#666',
          fontSize: 10
        }
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: [],
        itemStyle: {
          color: '#ef232a',
          color0: '#14b143',
          borderColor: '#ef232a',
          borderColor0: '#14b143'
        },
        emphasis: {
          itemStyle: {
            borderWidth: 2
          }
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: [],
        barMaxWidth: 10
      }
    ]
  }
  
  chartInstance.setOption(option)
  
  // 绑定事件
  bindChartEvents(chartInstance, index)
  
  // 更新数据
  updateChartData(index)
}

// 绑定图表事件
const bindChartEvents = (chartInstance, index) => {
  if (!chartInstance) return
  
  // 鼠标移动事件 - 更新涨幅显示
  chartInstance.on('mouseover', (params) => {
    if (params.componentType === 'series' && params.seriesName === 'K线') {
      const dataIndex = params.dataIndex
      updateChangeFromHover(index, dataIndex)
    }
  })
  
  // 鼠标移出事件
  chartInstance.on('globalout', () => {
    resetToTotalChange(index)
  })
  
  // 图表区域外的鼠标移出
  chartInstance.getZr().on('mouseout', (e) => {
    if (!e.target) {
      resetToTotalChange(index)
    }
  })
}

// 更新悬停点的涨幅计算
const updateChangeFromHover = (index, dataIndex) => {
  const stockData = stocksFullData.value[index]
  if (!stockData || dataIndex < 0 || dataIndex >= stockData.length) return
  
  const item = stockData[dataIndex]
  
  // 计算从悬停点到最新的涨幅
  if (stockData.length > 0) {
    const hoverOpen = item.open
    const latestClose = stockData[stockData.length - 1].close
    const changeFromHover = ((latestClose - hoverOpen) / hoverOpen) * 100
    displayedStocks.value[index].currentChange = changeFromHover
  }
}

// 重置为总涨幅
const resetToTotalChange = (index) => {
  const stockData = stocksFullData.value[index]
  if (stockData && stockData.length > 0) {
    const firstOpen = stockData[0].open
    const lastClose = stockData[stockData.length - 1].close
    const totalChange = ((lastClose - firstOpen) / firstOpen) * 100
    displayedStocks.value[index].currentChange = totalChange
  }
}

// 更新图表数据
const updateChartData = (index) => {
  const chartInstance = chartInstances.value[index]
  const stockData = stocksFullData.value[index]
  
  if (!chartInstance || !stockData || stockData.length === 0) return
  
  // 准备日期数据
  const dates = stockData.map(item => formatDate(item.date, query.value.freq))
  
  // 准备K线数据
  const klineData = stockData.map(item => [
    item.open,
    item.close,
    item.low,
    item.high
  ])
  
  // 准备成交量数据（带颜色）
  const volumeData = stockData.map(item => {
    const color = item.close >= item.open ? '#ef232a' : '#14b143'
    return {
      value: item.vol,
      itemStyle: { color }
    }
  })
  
  // 更新图表
  chartInstance.setOption({
    xAxis: [
      { data: dates },
      { data: dates }
    ],
    series: [
      { data: klineData },
      { data: volumeData }
    ]
  })
  
  // 初始化总涨幅
  resetToTotalChange(index)
}

const getGridColumns = () => {
  const count = displayedStocks.value.length
  if (count === 0) return 'none'
  if (count === 1) return '1fr'
  if (count === 2) return '1fr 1fr'
  if (count === 3) return '1fr 1fr 1fr'
  return '1fr 1fr'
}

const checkBackend = async () => {
  try {
    const response = await axios.get('/api/health')
    backendStatus.value = true
    redisStatus.value = response.data.redis || 'unknown'
  } catch (e) {
    backendStatus.value = false
    redisStatus.value = 'unknown'
  }
}

const handleFileUpload = (stocks, errorMsg) => {
  if (errorMsg) {
    error.value = 'Excel文件解析失败: ' + errorMsg
    return
  }
  importedStocks.value = stocks
  error.value = stocks.length > 0 ? '' : 'Excel文件中未找到有效的股票代码'
}

const clearImport = () => {
  importedStocks.value = []
  displayedStocks.value = []
  stocksFullData.value = []
  chartInstances.value.forEach(chart => chart && chart.dispose())
  chartInstances.value = []
  chartContainers.value = []
  if (queryFormRef.value && queryFormRef.value.fileInput) {
    queryFormRef.value.fileInput.value = ''
  }
}

const zoomAll = (start, end) => {
  chartInstances.value.forEach((chartInstance) => {
    if (chartInstance) {
      chartInstance.dispatchAction({
        type: 'dataZoom',
        start: start,
        end: end
      })
    }
  })
}

const updateStockChange = (index, change) => {
  if (displayedStocks.value[index]) {
    displayedStocks.value[index].totalChange = change
  }
}

const fetchKlineData = async () => {
  error.value = ''
  loading.value = true
  
  try {
    const startDate = query.value.startDate.replace(/-/g, '')
    const endDate = query.value.endDate.replace(/-/g, '')
    
    const stockCodes = []
    
    if (query.value.stock1) {
      stockCodes.push(query.value.stock1)
    }
    
    if (importedStocks.value.length > 0) {
      stockCodes.push(...importedStocks.value)
    }
    
    if (stockCodes.length === 0) {
      error.value = '请输入股票代码或导入Excel文件'
      loading.value = false
      return
    }
    
    const promises = stockCodes.map(code => 
      axios.get('/api/stock/kline', {
        params: {
          ts_code: code,
          freq: query.value.freq,
          start_date: startDate,
          end_date: endDate
        }
      }).catch(err => ({ error: true, code, message: err.message }))
    )
    
    const results = await Promise.all(promises)
    
    // 清理旧图表
    chartInstances.value.forEach(chart => chart && chart.dispose())
    chartInstances.value = []
    chartContainers.value = []
    
    const newDisplayedStocks = []
    const newStocksFullData = []
    
    results.forEach((result, index) => {
      if (result.error) {
        console.error(`股票 ${stockCodes[index]} 查询失败:`, result.message)
        return
      }
      
      if (result.data && result.data.code === 0) {
        const data = result.data.data
        const totalChange = data.length > 0 
          ? (((data[data.length - 1].close - data[0].open) / data[0].open) * 100)
          : 0
        
        newDisplayedStocks.push({
          code: stockCodes[index],
          name: result.data.name,
          info: result.data.info,
          totalChange: totalChange,
          currentChange: totalChange
        })
        
        newStocksFullData.push(data)
      }
    })
    
    displayedStocks.value = newDisplayedStocks
    stocksFullData.value = newStocksFullData
    
    await nextTick()
    
    // 初始化所有图表
    displayedStocks.value.forEach((_, index) => {
      initChart(index)
    })
    
  } catch (e) {
    error.value = '查询失败: ' + e.message
    console.error('查询错误:', e)
  } finally {
    loading.value = false
  }
}

// 监听周期变化
watch(() => query.value.freq, (newFreq) => {
  const dates = getDefaultDates(newFreq)
  query.value.startDate = dates.start
  query.value.endDate = dates.end
  
  if (displayedStocks.value.length > 0) {
    fetchKlineData()
  }
})

onMounted(() => {
  checkBackend()
})
</script>

<style scoped>
.home {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header h1 {
  font-size: 28px;
  color: #2c3e50;
  margin-bottom: 6px;
}

.header p {
  font-size: 14px;
  color: #7f8c8d;
}

.status-group {
  display: flex;
  flex-direction: row;
  gap: 12px;
  align-items: center;
}

.status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.status-text {
  font-size: 13px;
  color: #5a6c7d;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online {
  background-color: #27ae60;
}

.status-dot.offline {
  background-color: #e74c3c;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card {
  background: white;
  border-radius: 6px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.card h3 {
  font-size: 16px;
  margin-bottom: 12px;
  color: #2c3e50;
}

.charts-container {
  display: grid;
  gap: 16px;
  margin-top: 12px;
}

/* 股票图表容器样式 */
.stock-chart-container {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 16px;
  position: relative;
}

.stock-info-header {
  margin-bottom: 12px;
}

.stock-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.stock-name {
  font-size: 17px;
  font-weight: 600;
  color: #2c3e50;
}

.stock-code {
  font-size: 13px;
  color: #95a5a6;
}

.change-badge {
  font-size: 14px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 3px;
}

.change-badge.positive {
  color: #ef232a;
  background: rgba(239, 35, 42, 0.1);
}

.change-badge.negative {
  color: #14b143;
  background: rgba(20, 177, 67, 0.1);
}

.stock-metrics-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metric-label {
  font-size: 11px;
  color: #95a5a6;
}

.metric-value {
  font-size: 13px;
  font-weight: 600;
  color: #2c3e50;
}

.metric-value.positive {
  color: #ef232a;
}

.metric-value.negative {
  color: #14b143;
}

.chart-container {
  width: 100%;
  height: 320px;
}
</style>
