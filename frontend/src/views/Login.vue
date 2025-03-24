<template>
  <div class="login">
    <div class="row">
      <div class="col-md-6 offset-md-3">
        <div class="card">
          <div class="card-body">
            <h2 class="card-title mb-4 text-center">登录账户</h2>
            
            <form @submit.prevent="handleLogin">
              <div class="form-group mb-3">
                <label for="username">用户名</label>
                <input
                  id="username"
                  v-model="form.username"
                  type="text"
                  class="form-control"
                  required
                  placeholder="输入用户名"
                >
              </div>
              
              <div class="form-group mb-3">
                <label for="password">密码</label>
                <input
                  id="password"
                  v-model="form.password"
                  type="password"
                  class="form-control"
                  required
                  placeholder="输入密码"
                >
              </div>
              
              <div v-if="error" class="alert alert-danger">
                {{ error }}
              </div>
              
              <div class="d-grid">
                <button
                  type="submit"
                  class="btn btn-primary w-100"
                  :disabled="loading"
                >
                  <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  {{ loading ? '登录中...' : '登录' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoginPage',
  data() {
    return {
      form: {
        username: '',
        password: ''
      },
      loading: false,
      error: null
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.error = null
      
      try {
        await this.$store.dispatch('login', {
          username: this.form.username,
          password: this.form.password
        })
        
        // 重定向到来源页面或首页
        const redirectPath = this.$route.query.redirect || '/'
        this.$router.push(redirectPath)
      } catch (error) {
        console.error(error)
        this.error = '用户名或密码错误，请重试'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login {
  max-width: 100%;
  margin: 0 auto;
  padding: 20px;
}
</style> 