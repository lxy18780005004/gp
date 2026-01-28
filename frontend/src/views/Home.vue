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
          <StockChart
            v-for="(stock, index) in displayedStocks"
            :key="stock.code + '_' + index"
            :ref="setChartRef"
            :stock-info="stock"
            :stock-data="stocksFullData[index] || []"
            :freq="query.freq"
            :index="index"
            @update-change="updateStockChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import axios from 'axios'
import QueryForm from '../components/QueryForm.vue'
import StockChart from '../components/StockChart.vue'

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

// 图表引用 - 使用函数收集 refs
const chartRefs = ref([])

const setChartRef = (el) => {
  if (el && !chartRefs.value.includes(el)) {
    chartRefs.value.push(el)
  }
}

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
  chartRefs.value = []
  if (queryFormRef.value && queryFormRef.value.fileInput) {
    queryFormRef.value.fileInput.value = ''
  }
}

const zoomAll = (start, end) => {
  chartRefs.value.forEach((chartComp) => {
    if (chartComp && chartComp.chartInstance) {
      const instance = chartComp.chartInstance.value || chartComp.chartInstance
      if (instance) {
        instance.dispatchAction({
          type: 'dataZoom',
          start: start,
          end: end
        })
      }
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
    
    chartRefs.value = []
    
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
          ? (((data[data.length - 1].close - data[0].open) / data[0].open) * 100).toFixed(2)
          : 0
        
        newDisplayedStocks.push({
          code: stockCodes[index],
          name: result.data.name,
          info: result.data.info,
          totalChange: parseFloat(totalChange)
        })
        
        newStocksFullData.push(data)
      }
    })
    
    displayedStocks.value = newDisplayedStocks
    stocksFullData.value = newStocksFullData
    
    await nextTick()
    
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
</style>
