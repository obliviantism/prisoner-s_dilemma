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

// 添加全局错误处理
const app = createApp(App)

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
    console.error('Vue错误:', err)
    console.error('错误信息:', info)
}

app.use(router)
app.use(store)
app.mount('#app')
