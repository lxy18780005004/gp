<template>
  <div class="sidebar">
    <div class="logo">
      <el-icon :size="32" color="#409EFF"><TrendCharts /></el-icon>
      <span class="logo-text">CryptoTrade</span>
    </div>

    <el-menu
      :default-active="activeMenu"
      class="sidebar-menu"
      @select="handleMenuSelect"
    >
      <el-menu-item index="/">
        <el-icon><TrendCharts /></el-icon>
        <span>K线图</span>
      </el-menu-item>

      <el-menu-item index="/statistics">
        <el-icon><DataAnalysis /></el-icon>
        <span>统计</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { TrendCharts, DataAnalysis } from '@element-plus/icons-vue'

const props = defineProps({
  activeRoute: {
    type: String,
    default: '/'
  }
})

const emit = defineEmits(['navigate'])

const activeMenu = ref(props.activeRoute)

watch(() => props.activeRoute, (newVal) => {
  activeMenu.value = newVal
})

const handleMenuSelect = (index) => {
  activeMenu.value = index
  emit('navigate', index)
}
</script>

<style scoped>
.sidebar {
  width: 250px;
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
}

.el-menu-item {
  height: 56px;
  line-height: 56px;
}
</style>
