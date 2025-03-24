<template>
  <div class="login">
    <div class="row">
      <div class="col-md-6 offset-md-3">
        <div class="card">
          <div class="card-body">
            <h2 class="card-title mb-4 text-center">登录账户</h2>
            
            <b-form @submit.prevent="handleLogin">
              <b-form-group
                label="用户名"
                label-for="username"
              >
                <b-form-input
                  id="username"
                  v-model="form.username"
                  type="text"
                  required
                  placeholder="输入用户名"
                ></b-form-input>
              </b-form-group>
              
              <b-form-group
                label="密码"
                label-for="password"
              >
                <b-form-input
                  id="password"
                  v-model="form.password"
                  type="password"
                  required
                  placeholder="输入密码"
                ></b-form-input>
              </b-form-group>
              
              <b-alert
                v-if="error"
                variant="danger"
                show
              >
                {{ error }}
              </b-alert>
              
              <div class="d-grid">
                <b-button
                  type="submit"
                  variant="primary"
                  :disabled="loading"
                  class="w-100"
                >
                  <b-spinner v-if="loading" small></b-spinner>
                  {{ loading ? '登录中...' : '登录' }}
                </b-button>
              </div>
            </b-form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  name: 'Login',
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
    ...mapActions(['login']),
    
    async handleLogin() {
      this.loading = true
      this.error = null
      
      try {
        await this.login({
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
}
</style> 