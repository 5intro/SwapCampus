export const studentIdRule = {
  required: true,
  message: '请输入用户名',
  trigger: 'blur',
}

export const passwordRule = {
  required: true,
  min: 6,
  message: '密码至少 6 个字符',
  trigger: 'blur',
}

export const productTitleRules = [
  { required: true, message: '请输入商品标题', trigger: 'blur' },
  { min: 2, max: 200, message: '标题长度在 2 到 200 字符之间', trigger: 'blur' },
]

export const priceRules = [
  { required: true, message: '请输入售价', trigger: 'blur' },
  {
    pattern: /^\d+(\.\d{1,2})?$/,
    message: '价格最多两位小数',
    trigger: 'blur',
  },
]

export const conditionRules = [
  { required: true, message: '请选择成色', trigger: 'change' },
]
