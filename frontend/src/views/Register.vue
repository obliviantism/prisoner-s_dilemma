<template>
  <div class="register">
    <div class="row">
      <div class="col-md-6 offset-md-3">
        <div class="card">
          <div class="card-body">
            <h2 class="card-title mb-4 text-center">注册账户</h2>
            
            <form @submit.prevent="handleRegister">
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
                <label for="email">电子邮箱 (可选)</label>
                <input
                  id="email"
                  v-model="form.email"
                  type="email"
                  class="form-control"
                  placeholder="输入电子邮箱"
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
              
              <div class="form-group mb-3">
                <label for="password2">确认密码</label>
                <input
                  id="password2"
                  v-model="form.password2"
                  type="password"
                  class="form-control"
                  required
                  placeholder="再次输入密码"
                >
              </div>
              
              <div v-if="error" class="alert alert-danger mb-3">
                {{ error }}
              </div>
              
              <div class="d-grid">
                <button
                  type="submit"
                  class="btn btn-primary w-100"
                  :disabled="loading"
                >
                  <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  {{ loading ? '注册中...' : '注册' }}
                </button>
              </div>
              
              <div class="text-center mt-3">
                已有账户？
                <router-link to="/login">登录</router-link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  name: 'RegisterPage',
  data() {
    return {
      form: {
        username: '',
        email: '',
        password: '',
        password2: ''
      },
      loading: false,
      error: null
    }
  },
  methods: {
    ...mapActions(['register']),
    async handleRegister() {
      // 验证密码是否一致
      if (this.form.password !== this.form.password2) {
        this.error = '两次输入的密码不一致';
        return;
      }
      
      this.loading = true;
      this.error = null;
      
      try {
        await this.register({
          username: this.form.username,
          email: this.form.email,
          password: this.form.password
        });
        
        // 重定向到登录页面
        this.$router.push({ 
          name: 'Login',
          query: { registered: 'success' }
        });
      } catch (error) {
        if (error.response && error.response.data) {
          this.error = error.response.data.error || '注册失败，请稍后再试';
        } else {
          this.error = '注册失败，请稍后再试';
        }
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
.register {
  max-width: 100%;
  margin: 0 auto;
  padding: 20px;
}
</style> 