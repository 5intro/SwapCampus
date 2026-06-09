<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { uploadStudentIdCard, getVerificationStatus } from '@/api/users'
import { ElMessage } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const submitting = ref(false)
const imageFile = ref(null)
const statusText = ref('')
const statusType = ref('info')

onMounted(async () => {
  await refreshStatus()
})

async function refreshStatus() {
  loading.value = true
  try {
    await auth.fetchProfile()
    // 路由 /publish 的 requiresVerification 守卫会检查，但这里也做一次
  } catch { /* handled */ } finally {
    loading.value = false
    updateStatusDisplay()
  }
}

function updateStatusDisplay() {
  const status = auth.user?.verification_status
  switch (status) {
    case 'approved':
      statusText.value = '认证已通过，现在可以发布商品了'
      statusType.value = 'success'
      break
    case 'pending':
      statusText.value = '学生证已提交，请耐心等待管理员审核'
      statusType.value = 'warning'
      break
    case 'rejected':
      statusText.value = auth.user?.verification_note
        ? `认证未通过：${auth.user.verification_note}`
        : '认证未通过，请重新上传学生证'
      statusType.value = 'danger'
      break
    default:
      statusText.value = '请上传学生证照片完成认证'
      statusType.value = 'info'
      break
  }
}

function handleFileChange(file) {
  imageFile.value = file.raw
}

function beforeUpload(file) {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

async function handleSubmit() {
  if (!imageFile.value) {
    ElMessage.warning('请先选择学生证照片')
    return
  }
  submitting.value = true
  try {
    const formData = new FormData()
    formData.append('student_id_card', imageFile.value)
    await uploadStudentIdCard(formData)
    ElMessage.success('学生证已提交，请等待管理员审核')
    await refreshStatus()
  } catch {
    // handled by interceptor
  } finally {
    submitting.value = false
  }
}

function goToPublish() {
  router.push('/publish')
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card" v-loading="loading">
      <div class="auth-header">
        <span class="auth-icon">&#127891;</span>
        <h1>学生证认证</h1>
        <p>完成学生身份认证后即可发布商品</p>
      </div>

      <!-- 已通过 -->
      <div v-if="auth.user?.verification_status === 'approved'" class="status-area">
        <el-result icon="success" title="认证已通过" :sub-title="statusText">
          <template #extra>
            <el-button type="success" @click="goToPublish" round>去发布商品</el-button>
          </template>
        </el-result>
      </div>

      <!-- 审核中 -->
      <div v-else-if="auth.user?.verification_status === 'pending'" class="status-area">
        <el-result icon="warning" title="审核中" :sub-title="statusText" />
      </div>

      <!-- 已拒绝 -->
      <div v-else-if="auth.user?.verification_status === 'rejected'" class="status-area">
        <el-result icon="error" title="认证未通过" :sub-title="statusText" />
        <div class="upload-section">
          <p class="re-upload-hint">请重新上传清晰的学生证照片</p>
          <el-upload
            :auto-upload="false"
            :limit="1"
            :before-upload="beforeUpload"
            :on-change="handleFileChange"
            :file-list="[]"
            drag
            accept="image/*"
          >
            <el-icon class="el-icon--upload"><!-- upload icon --></el-icon>
            <div class="el-upload__text">
              将学生证照片拖到此处，或<em>点击上传</em>
            </div>
          </el-upload>
          <el-button
            type="success"
            :loading="submitting"
            @click="handleSubmit"
            round
            class="auth-submit-btn"
            size="large"
          >
            重新提交认证
          </el-button>
        </div>
      </div>

      <!-- 未认证 -->
      <div v-else class="upload-section">
        <el-alert
          :title="statusText"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 24px"
        />
        <el-upload
          :auto-upload="false"
          :limit="1"
          :before-upload="beforeUpload"
          :on-change="handleFileChange"
          :file-list="[]"
          drag
          accept="image/*"
        >
          <el-icon class="el-icon--upload"><!-- upload icon --></el-icon>
          <div class="el-upload__text">
            将学生证照片拖到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              仅支持 JPG/PNG 格式，大小不超过 5MB
            </div>
          </template>
        </el-upload>
        <el-button
          type="success"
          :loading="submitting"
          @click="handleSubmit"
          round
          class="auth-submit-btn"
          size="large"
        >
          提交认证
        </el-button>
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
  max-width: 480px;
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

.status-area {
  text-align: center;
}

.upload-section {
  margin-top: 0;
}

.re-upload-hint {
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 16px;
}

.auth-submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  background: linear-gradient(135deg, #43a047, #2e7d32);
  border: none;
  margin-top: 16px;
}
</style>
