<template>
  <div v-if="error" class="error-boundary">
    <div class="error-card">
      <h2 class="error-title">出错了</h2>
      <div class="error-message">
        <p>抱歉，应用程序遇到了意外错误。</p>
        <pre class="error-details">{{ error }}</pre>
      </div>
      <div class="error-actions">
        <button class="btn btn-primary" @click="resetError">重试</button>
      </div>
    </div>
  </div>
  <slot v-else></slot>
</template>

<script>
export default {
  name: 'ErrorBoundary',
  data() {
    return {
      error: null
    }
  },
  methods: {
    resetError() {
      this.error = null
      if (this.$router) {
        this.$router.go(0) // 刷新当前页面
      }
    }
  },
  errorCaptured(err, vm, info) {
    this.error = `${err.stack}\n\n错误信息: ${info}`
    return false // 防止错误继续传播
  }
}
</script>

<style scoped>
.error-boundary {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.error-card {
  background-color: white;
  border-radius: 5px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 800px;
  padding: 20px;
  text-align: center;
}

.error-title {
  color: #dc3545;
  margin-bottom: 20px;
}

.error-message {
  margin-bottom: 20px;
  text-align: left;
}

.error-details {
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 5px;
  white-space: pre-wrap;
  overflow-x: auto;
  font-size: 12px;
  text-align: left;
}

.error-actions {
  margin-top: 20px;
}
</style> 