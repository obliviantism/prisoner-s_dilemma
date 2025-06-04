<template>
  <div id="app">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container">
        <router-link class="navbar-brand" to="/">囚徒困境</router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="切换导航">
          <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav" v-if="isAuthenticated">
            <li class="nav-item">
              <router-link class="nav-link" to="/strategies">策略</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/games">游戏</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/tournaments">锦标赛</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/leaderboard">排行榜</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/history">历史记录</router-link>
            </li>
          </ul>
          
          <!-- 已登录用户菜单 - 使用Vue控制下拉菜单 -->
          <ul class="navbar-nav ms-auto" v-if="isAuthenticated">
            <li class="nav-item dropdown" ref="userDropdown">
              <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" 
                 @click.prevent="toggleDropdown"
                 role="button">
                <i class="bi bi-person-circle me-1"></i> {{ currentUser ? currentUser.username : '用户' }}
              </a>
              <ul class="dropdown-menu dropdown-menu-end" :class="{ show: dropdownOpen }" 
                  style="position: absolute;" aria-labelledby="navbarDropdown">
                <li>
                  <a class="dropdown-item d-flex align-items-center" href="#" @click.prevent="handleLogout">
                    <i class="bi bi-box-arrow-right me-2"></i> 退出登录
                  </a>
                </li>
              </ul>
            </li>
          </ul>
          
          <!-- 未登录用户菜单 -->
          <ul class="navbar-nav ms-auto" v-else>
            <li class="nav-item">
              <router-link class="nav-link" to="/login">登录</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/register">注册</router-link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
    
    <div class="container py-4">
      <div class="alert alert-dismissible fade show" 
           :class="'alert-' + alertVariant" 
           v-if="showAlert" 
           role="alert">
        {{ alertMessage }}
        <button type="button" class="btn-close" @click="showAlert = false" aria-label="关闭"></button>
      </div>
      
      <router-view @alert="showGlobalAlert"></router-view>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  name: 'App',
  data() {
    return {
      showAlert: false,
      alertMessage: '',
      alertVariant: 'info',
      sessionChecked: false,
      dropdownOpen: false
    }
  },
  computed: {
    isAuthenticated() {
      return this.$store.getters.isAuthenticated
    },
    currentUser() {
      return this.$store.getters.currentUser
    }
  },
  methods: {
    ...mapActions(['restoreSession', 'logout']),
    async checkSession() {
      try {
        await this.restoreSession();
      } catch (error) {
        console.error('恢复会话失败:', error);
      } finally {
        this.sessionChecked = true;
      }
    },
    async handleLogout() {
      this.dropdownOpen = false;
      try {
        await this.logout();
        this.$router.push('/login');
        this.showGlobalAlert('已成功退出登录', 'success');
      } catch (error) {
        console.error('退出登录时发生错误:', error);
        this.showGlobalAlert('退出登录时发生错误，请重试', 'danger');
      }
    },
    showGlobalAlert(message, variant = 'info') {
      this.alertMessage = message;
      this.alertVariant = variant;
      this.showAlert = true;
    },
    toggleDropdown() {
      this.dropdownOpen = !this.dropdownOpen;
    },
    closeDropdown(e) {
      if (this.$refs.userDropdown && !this.$refs.userDropdown.contains(e.target)) {
        this.dropdownOpen = false;
      }
    }
  },
  async created() {
    await this.checkSession();
  },
  mounted() {
    // 点击其他地方关闭下拉菜单
    document.addEventListener('click', this.closeDropdown);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.closeDropdown);
  }
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
}

/* 确保下拉菜单正确显示 */
.dropdown-menu.show {
  display: block;
}
</style> 