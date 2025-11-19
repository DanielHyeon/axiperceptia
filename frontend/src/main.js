import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './assets/design.css'
import App from './App.vue'
import axios from 'axios'

// Vue Flow CSS imports
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

// Axios 기본 설정
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const app = createApp(App)
app.mount('#app')
