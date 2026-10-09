<template>
  <div class="app-layout" :class="{ 'login-layout': route.name === 'login' }">
    <Sidebar v-if="route.name !== 'login'" />
    <div class="main-content">
      <RouterView v-slot="{ Component }">
        <Transition name="fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </div>
    <ToastContainer />
    <MobileNav v-if="route.name !== 'login'" />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import Sidebar from '@/components/layout/Sidebar.vue'
import MobileNav from '@/components/layout/MobileNav.vue'
import ToastContainer from '@/components/layout/ToastContainer.vue'

const route = useRoute()
</script>
