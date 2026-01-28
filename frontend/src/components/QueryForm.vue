<template>
  <div class="query-form">
    <div class="form-row-single">
      <div class="form-group-compact">
        <label>股票代码:</label>
        <el-input 
          v-model="localQuery.stock1" 
          placeholder="例如: 000001.SZ"
          clearable
          style="width: 100%;"
        />
      </div>
      <div class="form-group-compact">
        <label>导入Excel:</label>
        <input 
          type="file" 
          accept=".xlsx,.xls" 
          @change="handleFileUpload"
          ref="fileInput"
          class="file-input"
        />
      </div>
      <button @click="$emit('clear-import')" class="btn-clear" v-if="importedCount > 0">
        清除导入 ({{ importedCount }}个)
      </button>
      <div class="form-group-compact">
        <label>日期范围:</label>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 280px;"
          @change="handleDateChange"
        />
      </div>
      <el-button 
        type="primary" 
        @click="$emit('query')" 
        :loading="loading"
      >
        {{ loading ? '查询中...' : '查询' }}
      </el-button>
    </div>
    
    <div class="form-row" style="margin-top: 12px;">
      <div class="form-group">
        <label style="margin-right: 12px;">周期:</label>
        <el-radio-group v-model="localQuery.freq" size="default">
          <el-radio-button label="D">日线</el-radio-button>
          <el-radio-button label="W">周线</el-radio-button>
          <el-radio-button label="M">月线</el-radio-button>
        </el-radio-group>
      </div>
      <div class="form-group" v-if="showZoomControls" style="margin-left: 40px;">
        <label style="margin-right: 12px;">统一缩放:</label>
        <el-button-group>
          <el-button size="small" @click="$emit('zoom-all', 0, 100)">显示全部</el-button>
          <el-button size="small" @click="$emit('zoom-all', 70, 100)">最近30%</el-button>
          <el-button size="small" @click="$emit('zoom-all', 85, 100)">最近15%</el-button>
          <el-button size="small" @click="$emit('zoom-all', 0, 30)">最早30%</el-button>
        </el-button-group>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import * as XLSX from 'xlsx'

const props = defineProps({
  query: Object,
  loading: Boolean,
  importedCount: Number,
  showZoomControls: Boolean
})

const emit = defineEmits(['update:query', 'file-upload', 'clear-import', 'query', 'zoom-all'])

const fileInput = ref(null)
const localQuery = ref({ ...props.query })

// 日期范围计算属性
const dateRange = computed({
  get() {
    return [localQuery.value.startDate, localQuery.value.endDate]
  },
  set(val) {
    if (val && val.length === 2) {
      localQuery.value.startDate = val[0]
      localQuery.value.endDate = val[1]
    }
  }
})

const handleDateChange = (val) => {
  if (val && val.length === 2) {
    localQuery.value.startDate = val[0]
    localQuery.value.endDate = val[1]
  }
}

watch(() => props.query, (newVal) => {
  localQuery.value = { ...newVal }
}, { deep: true })

watch(localQuery, (newVal) => {
  emit('update:query', newVal)
}, { deep: true })

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target.result)
      const workbook = XLSX.read(data, { type: 'array' })
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
      const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 })
      
      const stocks = []
      for (let i = 0; i < jsonData.length; i++) {
        const code = jsonData[i][0]
        if (code && typeof code === 'string' && code.trim()) {
          stocks.push(code.trim())
        }
      }
      
      emit('file-upload', stocks)
    } catch (err) {
      console.error('Excel解析错误:', err)
      emit('file-upload', [], err.message)
    }
  }
  reader.readAsArrayBuffer(file)
}

defineExpose({ fileInput })
</script>

<style scoped>
.query-form {
  margin-bottom: 16px;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  align-items: center;
}

.form-row-single {
  display: flex;
  gap: 12px;
  align-items: center;
}

.form-group {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
}

.form-group-compact {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.form-group-compact:nth-child(1) {
  flex: 0 0 220px;
}

.form-group-compact:nth-child(2) {
  flex: 0 0 240px;
}

.form-group-compact:nth-child(3) {
  flex: 0 0 auto;
  min-width: 0;
}

.form-group label,
.form-group-compact label {
  display: block;
  margin-bottom: 0;
  color: #2c3e50;
  font-weight: 500;
  font-size: 13px;
  white-space: nowrap;
  flex-shrink: 0;
}

.file-input {
  width: 100%;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}

.btn-clear {
  padding: 6px 12px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.3s;
  white-space: nowrap;
}

.btn-clear:hover {
  background-color: #c0392b;
}
</style>
