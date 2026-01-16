<script setup lang="ts">
import { ref } from 'vue'
import api, { setToken } from '../api'

const username = ref('admin')
const password = ref('admin123')
const msg = ref('')
const loading = ref(false)

const emit = defineEmits<{ (e: 'logged-in'): void }>()

async function onLogin() {
  msg.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/auth/login', { username: username.value, password: password.value })
    setToken(data.access_token)
    emit('logged-in')
  } catch (e: any) {
    msg.value = e?.response?.data?.detail ?? String(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <div class="login-card">
      <h2>登录 - 实验组绘图平台</h2>
      <div class="hint">默认管理员账号用于首次登录（可在后端环境变量中修改）。</div>
      <div style="display:flex; flex-direction:column; gap:10px;">
        <input class="input" v-model="username" placeholder="用户名" />
        <input class="input" v-model="password" placeholder="密码" type="password" />
        <div class="actions">
          <button class="btn2" :disabled="loading" @click="onLogin">登录</button>
          <button class="btn2 secondary" :disabled="loading" @click="() => { username='admin'; password='admin123' }">填充默认</button>
        </div>
        <div class="msg" v-if="msg">{{ msg }}</div>
      </div>
    </div>
  </div>
</template>
