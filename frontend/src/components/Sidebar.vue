<template>
  <div class="sidebar">
    <div class="logo">
      <h2>Tushare</h2>
    </div>
    <nav class="menu">
      <div 
        v-for="item in menuItems" 
        :key="item.id"
        :class="['menu-item', { active: activeMenu === item.id }]"
        @click="activeMenu = item.id"
      >
        <span class="icon">{{ item.icon }}</span>
        <span class="label">{{ item.label }}</span>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const activeMenu = ref('home')

const menuItems = [
  { id: 'home', label: '首页', icon: '🏠' },
  { id: 'stocks', label: '股票列表', icon: '📊' },
  { id: 'market', label: '市场行情', icon: '📈' },
  { id: 'analysis', label: '数据分析', icon: '🔍' },
  { id: 'settings', label: '设置', icon: '⚙️' }
]
</script>

<style scoped>
.sidebar {
  width: 220px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h2 {
  font-size: 24px;
  font-weight: 600;
}

.menu {
  flex: 1;
  padding: 20px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 14px 20px;
  cursor: pointer;
  transition: all 0.3s;
  color: rgba(255, 255, 255, 0.7);
}

.menu-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.menu-item.active {
  background-color: #3498db;
  color: white;
}

.icon {
  font-size: 20px;
  margin-right: 12px;
}

.label {
  font-size: 15px;
}
</style>
