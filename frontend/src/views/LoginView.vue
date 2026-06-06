<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { studentIdRule, passwordRule } from '@/utils/validators'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.login(form)
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch {
    ElMessage.error('学号或密码错误')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-header">
        <span class="auth-icon">&#127795;</span>
        <h1>SwapCampus</h1>
        <p>校园闲置物品交易平台</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="{ username: [studentIdRule], password: [passwordRule] }"
        label-position="top"
        size="large"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="学号" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入学号"
            :prefix-icon="User"
            maxlength="9"
            autocomplete="username"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            autocomplete="current-password"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="success"
            :loading="loading"
            @click="handleLogin"
            class="auth-submit-btn"
            round
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        还没有账号？
        <router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 30%, #f1f8e9 70%, #fff9c4 100%);
  padding: 20px;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 16px;
  padding: 40px 36px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-icon {
  font-size: 40px;
}

.auth-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 8px 0 4px;
}

.auth-header p {
  font-size: 14px;
  color: var(--text-secondary);
}

.auth-submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  background: linear-gradient(135deg, #43a047, #2e7d32);
  border: none;
}

.auth-submit-btn:hover {
  background: linear-gradient(135deg, #388e3c, #1b5e20);
}

.auth-footer {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
}

.auth-footer a {
  color: #43a047;
  font-weight: 600;
}
</style>
