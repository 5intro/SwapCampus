<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Navbar from '@/components/layout/Navbar.vue'
import Footer from '@/components/layout/Footer.vue'

const auth = useAuthStore()
const route = useRoute()
auth.checkAuth()

const layout = computed(() => route.meta.layout || 'default')
</script>

<template>
  <Navbar v-if="layout !== 'blank'" />
  <main :class="{ 'main-chat': layout === 'chat' }">
    <router-view />
  </main>
  <Footer v-if="layout !== 'blank' && layout !== 'chat'" />
</template>

<style>
.main-chat {
  height: calc(100dvh - 60px);
  overflow: hidden;
}
</style>
