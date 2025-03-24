<template>
  <div id="app">
    <b-navbar toggleable="lg" type="dark" variant="dark">
      <b-container>
        <b-navbar-brand to="/">囚徒困境</b-navbar-brand>
        <b-navbar-toggle target="nav-collapse"></b-navbar-toggle>
        
        <b-collapse id="nav-collapse" is-nav>
          <b-navbar-nav v-if="isAuthenticated">
            <b-nav-item to="/strategies">策略</b-nav-item>
            <b-nav-item to="/games">游戏</b-nav-item>
            <b-nav-item to="/leaderboard">排行榜</b-nav-item>
          </b-navbar-nav>
          
          <b-navbar-nav class="ml-auto" v-if="isAuthenticated">
            <b-nav-item-dropdown right>
              <template #button-content>
                <b-icon icon="person-fill"></b-icon> {{ currentUser ? currentUser.username : '用户' }}
              </template>
              <b-dropdown-item @click="logout">退出登录</b-dropdown-item>
            </b-nav-item-dropdown>
          </b-navbar-nav>
          
          <b-navbar-nav class="ml-auto" v-else>
            <b-nav-item to="/login">登录</b-nav-item>
          </b-navbar-nav>
        </b-collapse>
      </b-container>
    </b-navbar>
    
    <b-container class="py-4">
      <b-alert
        v-model="showAlert"
        dismissible
        fade
        :variant="alertVariant"
      >
        {{ alertMessage }}
      </b-alert>
      
      <router-view @alert="showGlobalAlert"></router-view>
    </b-container>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'App',
  data() {
    return {
      showAlert: false,
      alertMessage: '',
      alertVariant: 'info'
    }
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'currentUser'])
  },
  methods: {
    ...mapActions(['logout']),
    
    showGlobalAlert(message, variant = 'info') {
      this.alertMessage = message
      this.alertVariant = variant
      this.showAlert = true
    }
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

.ml-auto {
  margin-left: auto !important;
}
</style>
