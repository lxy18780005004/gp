<template>
  <div class="statistics-page">
    <!-- 查询表单 -->
    <el-card class="query-card">
      <div class="query-section">
        <div class="input-row">
          <div>
            <el-input 
                v-model="queryForm.ts_codes" 
                placeholder="输入股票代码，多个代码用逗号分隔"
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
            class="date-picker"
          />
          
          <el-button 
            type="primary" 
            @click="calculateStatistics" 
            :loading="loading"
          >
            <el-icon><DataAnalysis /></el-icon>
            计算统计
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
      </div>
    </el-card>

    <!-- 统计结果 -->
    <el-card class="result-card" v-if="statisticsResult">
      <template #header>
        <div class="card-header">
          <span>统计结果</span>
          <el-tag :type="statisticsResult.avgChange >= 0 ? 'success' : 'danger'" size="large">
            平均涨幅: {{ statisticsResult.avgChange >= 0 ? '+' : '' }}{{ statisticsResult.avgChange }}%
          </el-tag>
        </div>
      </template>
      
      <div class="summary-info">
        <el-descriptions :column="4" border>
          <el-descriptions-item label="统计股票数">{{ statisticsResult.totalCount }}</el-descriptions-item>
          <el-descriptions-item label="上涨股票数">
            <span class="positive">{{ statisticsResult.upCount }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="下跌股票数">
            <span class="negative">{{ statisticsResult.downCount }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="平盘股票数">{{ statisticsResult.flatCount }}</el-descriptions-item>
          <el-descriptions-item label="最大涨幅">
            <span class="positive">+{{ statisticsResult.maxChange }}%</span>
          </el-descriptions-item>
          <el-descriptions-item label="最大跌幅">
            <span class="negative">{{ statisticsResult.minChange }}%</span>
          </el-descriptions-item>
          <el-descriptions-item label="中位数涨幅">
            <span :class="statisticsResult.medianChange >= 0 ? 'positive' : 'negative'">
              {{ statisticsResult.medianChange >= 0 ? '+' : '' }}{{ statisticsResult.medianChange }}%
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="统计周期">
            {{ queryForm.start_date }} ~ {{ queryForm.end_date }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 详细列表 -->
      <div class="detail-table">
        <div class="table-header">
          <h3>股票详情</h3>
          <el-button 
            type="primary" 
            @click="viewKlineCharts"
            :disabled="!statisticsResult || statisticsResult.details.length === 0"
          >
            <el-icon><TrendCharts /></el-icon>
            查看K线图
          </el-button>
        </div>
        <el-table :data="statisticsResult.details" stripe style="width: 100%" max-height="500">
          <el-table-column type="index" label="序号" width="60" />
          <el-table-column prop="ts_code" label="股票代码" width="120" />
          <el-table-column prop="name" label="股票名称" width="150" />
          <el-table-column prop="startPrice" label="起始价格" width="120">
            <template #default="scope">
              {{ scope.row.startPrice.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="endPrice" label="结束价格" width="120">
            <template #default="scope">
              {{ scope.row.endPrice.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="change" label="涨跌幅" width="120" sortable>
            <template #default="scope">
              <span :class="scope.row.change >= 0 ? 'positive' : 'negative'">
                {{ scope.row.change >= 0 ? '+' : '' }}{{ scope.row.change }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.change > 0 ? 'success' : scope.row.change < 0 ? 'danger' : 'info'" size="small">
                {{ scope.row.change > 0 ? '上涨' : scope.row.change < 0 ? '下跌' : '平盘' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error" label="备注" />
        </el-table>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty 
      v-if="!statisticsResult && !loading" 
      description="请输入股票代码或导入Excel文件进行统计分析"
      :image-size="150"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { DataAnalysis, Upload, TrendCharts } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import * as XLSX from 'xlsx'

const router = useRouter()
const API_BASE_URL = 'http://localhost:5000'

const queryForm = ref({
  ts_codes: '',
  start_date: '20250101',
  end_date: '20260128'
})

const dateRange = ref(['20250101', '20260128'])
const loading = ref(false)
const uploadRef = ref(null)
const statisticsResult = ref(null)

// 更新日期范围
const updateDateRange = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    queryForm.value.start_date = dateRange.value[0]
    queryForm.value.end_date = dateRange.value[1]
  }
}

// 获取单个股票的涨幅
const fetchSingleStockChange = async (ts_code) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/stock/kline`, {
      params: {
        ts_code,
        freq: 'D',
        start_date: queryForm.value.start_date,
        end_date: queryForm.value.end_date
      }
    })
    
    if (response.data.code === 0 && response.data.data.length > 0) {
      const data = response.data.data
      const name = response.data.name
      
      // 第一天的开盘价和最后一天的收盘价
      const startPrice = data[0].open
      const endPrice = data[data.length - 1].close
      
      // 计算涨跌幅
      const change = ((endPrice - startPrice) / startPrice * 100).toFixed(2)
      
      return {
        ts_code,
        name,
        startPrice,
        endPrice,
        change: parseFloat(change),
        error: null
      }
    } else {
      return {
        ts_code,
        name: '未知',
        startPrice: 0,
        endPrice: 0,
        change: 0,
        error: '无数据'
      }
    }
  } catch (error) {
    console.error(`查询 ${ts_code} 失败:`, error)
    return {
      ts_code,
      name: '未知',
      startPrice: 0,
      endPrice: 0,
      change: 0,
      error: '查询失败'
    }
  }
}

// 计算统计数据
const calculateStatistics = async () => {
  if (!queryForm.value.ts_codes) {
    ElMessage.warning('请输入股票代码')
    return
  }
  
  updateDateRange()
  
  // 分割股票代码
  const codes = queryForm.value.ts_codes.split(/[,，\s]+/).filter(code => code.trim())
  
  if (codes.length === 0) {
    ElMessage.warning('请输入有效的股票代码')
    return
  }
  
  loading.value = true
  statisticsResult.value = null
  
  try {
    // 并发请求所有股票数据
    const promises = codes.map(code => fetchSingleStockChange(code.trim()))
    const results = await Promise.all(promises)
    
    // 过滤掉查询失败的股票
    const validResults = results.filter(r => !r.error)
    
    if (validResults.length === 0) {
      ElMessage.warning('未查询到任何有效数据')
      return
    }
    
    // 计算统计数据
    const changes = validResults.map(r => r.change)
    const avgChange = (changes.reduce((sum, val) => sum + val, 0) / changes.length).toFixed(2)
    const maxChange = Math.max(...changes).toFixed(2)
    const minChange = Math.min(...changes).toFixed(2)
    
    // 计算中位数
    const sortedChanges = [...changes].sort((a, b) => a - b)
    const mid = Math.floor(sortedChanges.length / 2)
    const medianChange = sortedChanges.length % 2 === 0
      ? ((sortedChanges[mid - 1] + sortedChanges[mid]) / 2).toFixed(2)
      : sortedChanges[mid].toFixed(2)
    
    // 统计上涨、下跌、平盘数量
    const upCount = changes.filter(c => c > 0).length
    const downCount = changes.filter(c => c < 0).length
    const flatCount = changes.filter(c => c === 0).length
    
    statisticsResult.value = {
      totalCount: results.length,
      avgChange: parseFloat(avgChange),
      maxChange: parseFloat(maxChange),
      minChange: parseFloat(minChange),
      medianChange: parseFloat(medianChange),
      upCount,
      downCount,
      flatCount,
      details: results.sort((a, b) => b.change - a.change) // 按涨幅降序排列
    }
    
    ElMessage.success(`统计完成！共分析 ${results.length} 只股票`)
  } catch (error) {
    console.error('统计失败:', error)
    ElMessage.error('统计失败，请检查后端服务是否启动')
  } finally {
    loading.value = false
  }
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
      
      // 设置到查询表单并执行统计
      queryForm.value.ts_codes = codes.join(',')
      await calculateStatistics()
      
    } catch (error) {
      console.error('Excel解析失败:', error)
      ElMessage.error('Excel文件解析失败')
    }
  }
  
  reader.readAsArrayBuffer(file.raw)
}

// 跳转到K线图页面
const viewKlineCharts = () => {
  if (!statisticsResult.value || statisticsResult.value.details.length === 0) {
    ElMessage.warning('没有可查看的数据')
    return
  }
  
  // 提取股票代码列表（按当前排序顺序）
  const codes = statisticsResult.value.details
    .filter(item => !item.error) // 过滤掉有错误的股票
    .map(item => item.ts_code)
    .join(',')
  
  if (!codes) {
    ElMessage.warning('没有有效的股票代码')
    return
  }
  
  // 跳转到K线图页面，并传递参数
  router.push({
    path: '/',
    query: {
      codes: codes,
      start_date: queryForm.value.start_date,
      end_date: queryForm.value.end_date,
      autoLoad: 'true'
    }
  })
}
</script>

<style scoped>
.statistics-page {
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
  white-space: nowrap;
}

.input-row > * {
  display: inline-block;
  vertical-align: middle;
  margin-right: 10px;
}

.code-input {
  width: 350px;
  flex-shrink: 0;
}

.code-input :deep(.el-input-group) {
  width: 350px !important;
}

.code-input :deep(.el-input__wrapper) {
  width: 100% !important;
  transition: none !important;
}

.date-picker {
  width: 200px !important;
  flex-shrink: 0;
}

.date-picker :deep(.el-range-editor) {
  width: 200px !important;
  transition: none !important;
}

.result-card {
  flex: 1;
  overflow-y: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-info {
  margin-bottom: 30px;
}

.detail-table h3 {
  margin-bottom: 15px;
  color: #303133;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.table-header h3 {
  margin: 0;
}

.positive {
  color: #ec0000;
  font-weight: bold;
}

.negative {
  color: #00da3c;
  font-weight: bold;
}
</style>
