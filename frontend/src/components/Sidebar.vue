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
      <el-menu-item index="home">
        <el-icon><HomeFilled /></el-icon>
        <span>首页</span>
      </el-menu-item>

      <el-menu-item index="market">
        <el-icon><TrendCharts /></el-icon>
        <span>行情</span>
      </el-menu-item>

      <el-menu-item index="trade">
        <el-icon><Coin /></el-icon>
        <span>交易</span>
      </el-menu-item>

      <el-menu-item index="assets">
        <el-icon><Wallet /></el-icon>
        <span>资产</span>
      </el-menu-item>

      <el-menu-item index="orders">
        <el-icon><Document /></el-icon>
        <span>订单</span>
      </el-menu-item>

      <el-menu-item index="settings">
        <el-icon><Setting /></el-icon>
        <span>设置</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { HomeFilled, TrendCharts, Coin, Wallet, Document, Setting } from '@element-plus/icons-vue'

const activeMenu = ref('home')

const handleMenuSelect = (index) => {
  activeMenu.value = index
  console.log('Selected menu:', index)
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
