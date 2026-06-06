<script setup>
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { ElMessage } from 'element-plus'
import { Search, Bell } from '@element-plus/icons-vue'
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const chat = useChatStore()
const router = useRouter()
const searchKeyword = ref('')
const showMobileMenu = ref(false)
let pollTimer = null

onMounted(() => {
  if (auth.isLoggedIn) {
    chat.fetchConversations()
    // 每 15 秒刷新未读计数
    pollTimer = setInterval(() => chat.fetchConversations(), 15000)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

function goSearch() {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/search', query: { q: searchKeyword.value.trim() } })
  }
}

function logout() {
  auth.logout()
  ElMessage.success('已退出登录')
}
</script>

<template>
  <el-menu
    :default-active="router.currentRoute.value.path"
    mode="horizontal"
    :ellipsis="false"
    class="navbar"
    router
  >
    <div class="navbar-inner">
      <div class="navbar-left">
        <el-menu-item index="/" class="brand">
          <span class="brand-icon">&#127795;</span>
          <span class="brand-text">SwapCampus</span>
        </el-menu-item>
      </div>

      <div class="navbar-center">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索校园二手好物..."
          :prefix-icon="Search"
          size="large"
          class="search-input"
          @keyup.enter="goSearch"
          clearable
        />
      </div>

      <div class="navbar-right">
        <template v-if="auth.isLoggedIn">
          <el-menu-item index="/chat">
            <el-icon><component :is="'ChatDotRound'" /></el-icon>
            <span>消息</span>
            <el-badge
              v-if="chat.unreadTotal > 0"
              :value="chat.unreadTotal"
              class="unread-badge"
            />
          </el-menu-item>

          <el-menu-item index="/publish" class="publish-btn">
            <el-button type="success" round>
              <el-icon><component :is="'Plus'" /></el-icon>
              发布
            </el-button>
          </el-menu-item>

          <el-sub-menu index="user-menu">
            <template #title>
              <el-avatar
                :size="32"
                :src="auth.user?.avatar"
                class="nav-avatar"
              >
                {{ auth.user?.nickname?.[0] || auth.user?.username?.[0] || 'U' }}
              </el-avatar>
              <span class="nav-nickname">{{ auth.user?.nickname || auth.user?.username }}</span>
            </template>
            <el-menu-item index="/profile">个人主页</el-menu-item>
            <el-menu-item index="/my-products">我的商品</el-menu-item>
            <el-menu-item index="/my-orders">我的订单</el-menu-item>
            <el-menu-item @click="logout">退出登录</el-menu-item>
          </el-sub-menu>
        </template>

        <template v-else>
          <div class="nav-auth-buttons">
            <el-button
              class="btn-login"
              round
              @click="$router.push('/login')"
            >登录</el-button>
            <el-button
              type="success"
              round
              @click="$router.push('/register')"
            >注册</el-button>
          </div>
        </template>
      </div>
    </div>
  </el-menu>
</template>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
}

.navbar-inner {
  display: flex;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 0 16px;
  height: 60px;
}

.navbar-left {
  flex-shrink: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: none !important;
}

.brand-icon {
  font-size: 24px;
}

.brand-text {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #43a047, #2e7d32);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.navbar-center {
  flex: 1;
  max-width: 480px;
  margin: 0 24px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 24px;
  background: var(--bg-page);
}

.navbar-right {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.navbar-right .el-menu-item {
  border-bottom: none !important;
}

.publish-btn {
  border-bottom: none !important;
}

.nav-avatar {
  margin-right: 6px;
}

.nav-nickname {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-auth-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-login {
  color: var(--color-brand-dark);
  border-color: var(--color-brand);
  font-weight: 500;
}

.btn-login:hover {
  color: #fff;
  background: var(--color-brand);
  border-color: var(--color-brand);
}

.unread-badge {
  margin-left: 4px;
}

@media (max-width: 768px) {
  .navbar-center {
    display: none;
  }

  .nav-nickname {
    display: none;
  }
}
</style>
