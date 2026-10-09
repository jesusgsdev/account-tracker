<template>
  <div class="login-container">
    <div class="login-card card">
      <div class="login-header">
        <div class="logo-circle">📊</div>
        <h1 class="login-title">FolioTrack</h1>
        <p class="login-subtitle text-sm text-muted">Enter your credentials to access your net worth tracker</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div v-if="errorMsg" class="error-banner text-xs">
          <span>⚠️</span> {{ errorMsg }}
        </div>

        <div class="form-group">
          <label class="form-label" for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            class="form-input"
            placeholder="Enter username"
            required
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="form-input"
            placeholder="Enter password"
            required
            autocomplete="current-password"
          />
        </div>

        <button type="submit" class="btn btn-primary btn-login" :disabled="loading">
          {{ loading ? 'Authenticating…' : 'Sign In' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/client'

const router = useRouter()
const username = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    await authApi.login(username.value, password.value)
    password.value = ''
    router.push('/')
  } catch (e) {
    errorMsg.value = e instanceof Error ? e.message : 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  width: 100%;
  background: radial-gradient(circle at 50% 50%, #1f2937 0%, #111827 100%);
  padding: var(--space-4);
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: rgba(31, 41, 55, 0.4);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-xl);
  padding: var(--space-8) var(--space-6);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: var(--space-6);
}

.logo-circle {
  font-size: 2.5rem;
  margin-bottom: var(--space-3);
  display: inline-block;
}

.login-title {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  margin-bottom: var(--space-1);
}

.login-subtitle {
  line-height: 1.4;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.error-banner {
  background: var(--negative-bg);
  color: var(--negative);
  border: 1px solid rgba(239, 68, 68, 0.2);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.btn-login {
  width: 100%;
  justify-content: center;
  padding: var(--space-3);
  font-weight: 600;
  margin-top: var(--space-2);
}
</style>
