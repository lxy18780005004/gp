<template>
  <div class="app-container">
    <Sidebar />
    <div class="main-content">
      <Home />
    </div>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
import Home from './views/Home.vue'
</script>

<style scoped>
.app-container {
  display: flex;
  width: 100%;
  height: 100vh;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f5f5f5;
}
</style>
