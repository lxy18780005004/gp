<template>
  <div class="app-container">
    <Sidebar @navigate="handleNavigate" :active-route="currentRoute" />
    <div class="main-content">
      <StatusBar />
      <div class="content-wrapper">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import StatusBar from './components/StatusBar.vue'

const router = useRouter()
const route = useRoute()
const currentRoute = ref('/')

const handleNavigate = (path) => {
  router.push(path)
}

onMounted(() => {
  currentRoute.value = route.path
})

// 监听路由变化
router.afterEach((to) => {
  currentRoute.value = to.path
})
</script>

<style scoped>
.app-container {
  display: flex;
  width: 100%;
  height: 100vh;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
  overflow: hidden;
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
}
</style>
