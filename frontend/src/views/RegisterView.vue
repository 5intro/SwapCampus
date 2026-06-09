<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { studentIdRule, passwordRule } from '@/utils/validators'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  password_confirm: '',
  email: '',
  nickname: '',
  campus: '',
})

const passwordConfirmRule = {
  required: true,
  validator: (rule, value, callback) => {
    if (value !== form.password) {
      callback(new Error('两次密码输入不一致'))
    } else {
      callback()
    }
  },
  trigger: 'blur',
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.register({ ...form })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch {
    // handled by interceptor
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
        <h1>加入 SwapCampus</h1>
        <p>北京林业大学校园闲置交易平台</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        label-position="top"
        size="large"
        @submit.prevent="handleRegister"
      >
        <el-form-item label="用户名" prop="username" :rules="[studentIdRule]">
          <el-input
            v-model="form.username"
            placeholder="输入用户名"
          />
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="密码" prop="password" :rules="[passwordRule]">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="至少 6 位"
                show-password
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="确认密码" prop="password_confirm" :rules="[passwordConfirmRule]">
              <el-input
                v-model="form.password_confirm"
                type="password"
                placeholder="再次输入密码"
                show-password
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="昵称（选填）" prop="nickname">
          <el-input v-model="form.nickname" placeholder="给自己起个名字" maxlength="50" />
        </el-form-item>

        <el-form-item label="校区（选填）" prop="campus">
          <el-select v-model="form.campus" placeholder="选择校区" clearable style="width: 100%">
            <el-option label="校本部" value="校本部" />
            <el-option label="鹫峰校区" value="鹫峰校区" />
          </el-select>
        </el-form-item>

        <el-form-item label="邮箱（选填）" prop="email">
          <el-input
            v-model="form.email"
            placeholder="用于找回密码"
            type="email"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="success"
            :loading="loading"
            @click="handleRegister"
            class="auth-submit-btn"
            round
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="auth-footer">
        已有账号？
        <router-link to="/login">立即登录</router-link>
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
  max-width: 460px;
  background: #fff;
  border-radius: 16px;
  padding: 36px 36px 28px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.auth-header {
  text-align: center;
  margin-bottom: 24px;
}

.auth-icon {
  font-size: 36px;
}

.auth-header h1 {
  font-size: 22px;
  font-weight: 700;
  margin: 6px 0 2px;
}

.auth-header p {
  font-size: 13px;
  color: var(--text-secondary);
}

.auth-submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  background: linear-gradient(135deg, #43a047, #2e7d32);
  border: none;
  margin-top: 8px;
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
