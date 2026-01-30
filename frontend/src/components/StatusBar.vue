<template>
  <div class="status-bar">
    <div class="status-item">
      <el-tooltip :content="redisStatus === 'connected' ? 'Redis已连接' : 'Redis未连接'" placement="bottom">
        <div class="status-indicator">
          <span class="status-label">Redis:</span>
          <el-icon :size="16" :color="redisStatus === 'connected' ? '#67C23A' : '#F56C6C'">
            <CircleCheckFilled v-if="redisStatus === 'connected'" />
            <CircleCloseFilled v-else />
          </el-icon>
          <span :class="['status-text', redisStatus === 'connected' ? 'connected' : 'disconnected']">
            {{ redisStatus === 'connected' ? '已连接' : '未连接' }}
          </span>
        </div>
      </el-tooltip>
    </div>
    
    <div class="status-item">
      <el-tooltip :content="backendStatus === 'ok' ? '后端服务正常' : '后端服务异常'" placement="bottom">
        <div class="status-indicator">
          <span class="status-label">后端:</span>
          <el-icon :size="16" :color="backendStatus === 'ok' ? '#67C23A' : '#F56C6C'">
            <CircleCheckFilled v-if="backendStatus === 'ok'" />
            <CircleCloseFilled v-else />
          </el-icon>
          <span :class="['status-text', backendStatus === 'ok' ? 'connected' : 'disconnected']">
            {{ backendStatus === 'ok' ? '正常' : '异常' }}
          </span>
        </div>
      </el-tooltip>
    </div>
    
    <el-button 
      size="small" 
      :icon="Refresh" 
      circle 
      @click="checkStatus"
      :loading="loading"
      title="刷新状态"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { CircleCheckFilled, CircleCloseFilled, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000'

const redisStatus = ref('unknown')
const backendStatus = ref('unknown')
const loading = ref(false)
let intervalId = null

// 检查服务状态
const checkStatus = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/api/health`, {
      timeout: 3000
    })
    
    if (response.data.status === 'ok') {
      backendStatus.value = 'ok'
      redisStatus.value = response.data.redis || 'disconnected'
    } else {
      backendStatus.value = 'error'
      redisStatus.value = 'disconnected'
    }
  } catch (error) {
    console.error('健康检查失败:', error)
    backendStatus.value = 'error'
    redisStatus.value = 'disconnected'
  } finally {
    loading.value = false
  }
}

// 定时检查状态
onMounted(() => {
  checkStatus()
  // 每30秒检查一次
  intervalId = setInterval(checkStatus, 30000)
})

onBeforeUnmount(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 20px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.status-item {
  display: flex;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.status-text {
  font-size: 13px;
  font-weight: 500;
}

.status-text.connected {
  color: #67C23A;
}

.status-text.disconnected {
  color: #F56C6C;
}
</style>
