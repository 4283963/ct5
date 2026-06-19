<template>
  <div class="app-container">
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-icon class="logo-icon"><Ship /></el-icon>
          <h1 class="app-title">航线轨迹与燃油消耗效益分析系统</h1>
        </div>
        <div class="header-right">
          <span class="user-info">远洋货轮数据分析平台</span>
        </div>
      </el-header>

      <el-container>
        <el-aside width="220px" class="app-aside">
          <el-menu
            :default-active="activeMenu"
            router
            class="sidebar-menu"
            background-color="#001529"
            text-color="#fff"
            active-text-color="#409eff"
          >
            <el-menu-item index="/upload">
              <el-icon><Upload /></el-icon>
              <span>数据上传</span>
            </el-menu-item>
            <el-menu-item index="/dashboard">
              <el-icon><DataAnalysis /></el-icon>
              <span>指标看板</span>
            </el-menu-item>
            <el-menu-item index="/diagnosis">
              <el-icon><Warning /></el-icon>
              <span>诊断优化</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
}

.app-container {
  height: 100%;
}

.app-header {
  background: linear-gradient(90deg, #001529 0%, #002140 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 32px;
  color: #409eff;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.user-info {
  font-size: 14px;
  opacity: 0.85;
}

.app-aside {
  background: #001529;
  height: calc(100vh - 60px);
}

.sidebar-menu {
  border-right: none;
  height: 100%;
}

.app-main {
  background: #f0f2f5;
  padding: 20px;
  min-height: calc(100vh - 60px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
