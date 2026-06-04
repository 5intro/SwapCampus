<script setup>
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
auth.checkAuth()
</script>

<template>
  <router-view />
</template>
