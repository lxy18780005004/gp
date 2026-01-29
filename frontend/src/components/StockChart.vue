<template>
  <div class="stock-chart-container">
    <!-- 股票信息头部 -->
    <div class="stock-info-header">
      <div class="stock-title-row">
        <span class="stock-name">{{ stockInfo.name }}</span>
        <span class="stock-code">{{ stockInfo.code }}</span>
        <span 
          v-if="currentChange !== null" 
          :class="['change-badge', currentChange >= 0 ? 'positive' : 'negative']"
        >
          {{ currentChange >= 0 ? '+' : '' }}{{ currentChange.toFixed(2) }}%
        </span>
      </div>
      
      <div class="stock-metrics-row">
        <div class="metric-item">
          <span class="metric-label">最新</span>
          <span class="metric-value">{{ stockInfo.info.latest_price }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">涨跌</span>
          <span :class="['metric-value', stockInfo.info.change >= 0 ? 'positive' : 'negative']">
            {{ stockInfo.info.change >= 0 ? '+' : '' }}{{ stockInfo.info.change }}
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">幅度</span>
          <span :class="['metric-value', stockInfo.info.change_pct >= 0 ? 'positive' : 'negative']">
            {{ stockInfo.info.change_pct >= 0 ? '+' : '' }}{{ stockInfo.info.change_pct }}%
          </span>
        </div>
        <div class="metric-item">
          <span class="metric-label">最高</span>
          <span class="metric-value">{{ stockInfo.info.high }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">最低</span>
          <span class="metric-value">{{ stockInfo.info.low }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">成交量</span>
          <span class="metric-value">{{ formatNumber(stockInfo.info.volume) }}</span>
        </div>
      </div>
    </div>

    <!-- 图表容器 -->
    <div ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  stockInfo: {
    type: Object,
    required: true
  },
  stockData: {
    type: Array,
    default: () => []
  },
  freq: {
    type: String,
    default: 'D'
  },
  index: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update-change'])

// 响应式数据
const chartContainer = ref(null)
const chartInstance = ref(null)
const currentChange = ref(null)

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

// 初始化图表
const initChart = () => {
  if (!chartContainer.value) return
  
  // 销毁旧实例
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  
  // 创建新实例
  chartInstance.value = echarts.init(chartContainer.value)
  
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
        if (!props.stockData || dataIndex >= props.stockData.length) return ''
        
        const item = props.stockData[dataIndex]
        const dateLabel = formatDate(item.date, props.freq)
        
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
  
  chartInstance.value.setOption(option)
  
  // 绑定事件
  bindChartEvents()
}

// 绑定图表事件
const bindChartEvents = () => {
  if (!chartInstance.value) return
  
  // 鼠标移动事件 - 更新涨幅显示
  chartInstance.value.on('mouseover', (params) => {
    if (params.componentType === 'series' && params.seriesName === 'K线') {
      const dataIndex = params.dataIndex
      updateChangeFromHover(dataIndex)
    }
  })
  
  // 鼠标移出事件
  chartInstance.value.on('globalout', () => {
    resetToTotalChange()
  })
  
  // 图表区域外的鼠标移出
  chartInstance.value.getZr().on('mouseout', (e) => {
    if (!e.target) {
      resetToTotalChange()
    }
  })
}

// 更新悬停点的涨幅计算
const updateChangeFromHover = (dataIndex) => {
  if (!props.stockData || dataIndex < 0 || dataIndex >= props.stockData.length) return
  
  const item = props.stockData[dataIndex]
  
  // 计算从悬停点到最新的涨幅
  if (props.stockData.length > 0) {
    const hoverOpen = item.open
    const latestClose = props.stockData[props.stockData.length - 1].close
    const changeFromHover = ((latestClose - hoverOpen) / hoverOpen) * 100
    currentChange.value = changeFromHover
    emit('update-change', props.index, changeFromHover)
  }
}

// 重置为总涨幅
const resetToTotalChange = () => {
  if (props.stockData && props.stockData.length > 0) {
    const firstOpen = props.stockData[0].open
    const lastClose = props.stockData[props.stockData.length - 1].close
    const totalChange = ((lastClose - firstOpen) / firstOpen) * 100
    currentChange.value = totalChange
    emit('update-change', props.index, totalChange)
  }
}

// 更新图表数据
const updateChartData = () => {
  if (!chartInstance.value || !props.stockData || props.stockData.length === 0) return
  
  // 准备日期数据
  const dates = props.stockData.map(item => formatDate(item.date, props.freq))
  
  // 准备K线数据
  const klineData = props.stockData.map(item => [
    item.open,
    item.close,
    item.low,
    item.high
  ])
  
  // 准备成交量数据（带颜色）
  const volumeData = props.stockData.map(item => {
    const color = item.close >= item.open ? '#ef232a' : '#14b143'
    return {
      value: item.vol,
      itemStyle: { color }
    }
  })
  
  // 更新图表
  chartInstance.value.setOption({
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
  resetToTotalChange()
}

// 监听数据变化
watch(() => props.stockData, () => {
  nextTick(() => {
    updateChartData()
  })
}, { deep: true })

watch(() => props.freq, () => {
  nextTick(() => {
    updateChartData()
  })
})

// 生命周期
onMounted(() => {
  nextTick(() => {
    initChart()
    updateChartData()
  })
})

onBeforeUnmount(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null
  }
})

// 暴露实例供父组件使用
defineExpose({ 
  chartInstance,
  resetZoom: () => {
    if (chartInstance.value) {
      chartInstance.value.dispatchAction({
        type: 'dataZoom',
        start: 0,
        end: 100
      })
    }
  }
})
</script>

<style scoped>
.stock-chart-container {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 16px;
  position: relative;
}

/* 股票信息头部 */
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

/* 图表容器 */
.chart-container {
  width: 100%;
  height: 320px;
}
</style>
