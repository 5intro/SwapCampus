<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  max: {
    type: Number,
    default: 9,
  },
})

const emit = defineEmits(['update:modelValue'])

const fileList = ref([])

function handleChange(file, fileListLocal) {
  const raw = fileListLocal.map(f => f.raw).filter(Boolean)
  if (raw.length > props.max) {
    ElMessage.warning(`最多上传 ${props.max} 张图片`)
    return
  }
  emit('update:modelValue', raw)
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
</script>

<template>
  <el-upload
    v-model:file-list="fileList"
    action="#"
    list-type="picture-card"
    :auto-upload="false"
    :limit="max"
    :before-upload="beforeUpload"
    :on-change="handleChange"
  >
    <el-icon><Plus /></el-icon>
    <template #file="{ file }">
      <div>
        <img :src="file.url" class="upload-thumb" />
        <span class="el-upload-list__item-actions">
          <span class="el-upload-list__item-delete">
            <el-icon><Delete /></el-icon>
          </span>
        </span>
      </div>
    </template>
  </el-upload>
</template>

<style scoped>
.upload-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
