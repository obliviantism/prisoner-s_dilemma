import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

// 导入Bootstrap样式和JavaScript
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
// 导入Bootstrap Icons
import 'bootstrap-icons/font/bootstrap-icons.css'

// 全局确保Bootstrap在每个组件中可用
window.bootstrap = require('bootstrap/dist/js/bootstrap.bundle.min.js')

const app = createApp(App)

app.use(router)
app.use(store)
app.mount('#app')
