import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import monacoEditorPluginModule from 'vite-plugin-monaco-editor'

const monacoEditorPlugin = (monacoEditorPluginModule as any).default || monacoEditorPluginModule

export default defineConfig({
  plugins: [
    vue(),
    monacoEditorPlugin({})
  ],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  }
})
