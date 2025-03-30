<template>
  <div class="game-list">
    <h1>囚徒困境游戏</h1>
    <div class="action-buttons mb-4">
      <router-link to="/games/create" class="btn btn-primary">
        创建新游戏
      </router-link>
    </div>

    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="sr-only">加载中...</span>
      </div>
    </div>

    <div v-else-if="games.length === 0" class="alert alert-info">
      您还没有创建任何游戏。点击上方的"创建新游戏"按钮开始。
    </div>

    <div v-else class="game-table">
      <table class="table table-striped">
        <thead>
          <tr>
            <th>ID</th>
            <th>策略1</th>
            <th>策略2</th>
            <th>回合数</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="game in games" :key="game.id">
            <td>{{ game.id }}</td>
            <td>{{ game.strategy1 ? game.strategy1.name : '未知策略' }}</td>
            <td>{{ game.strategy2 ? game.strategy2.name : '未知策略' }}</td>
            <td>{{ game.current_round }} / {{ game.total_rounds }}</td>
            <td>{{ formatStatus(game.status) }}</td>
            <td>{{ formatDate(game.created_at) }}</td>
            <td>
              <router-link :to="`/games/${game.id}`" class="btn btn-sm btn-outline-primary">
                查看详情
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GameListView',
  data() {
    return {
      games: [],
      loading: true
    }
  },
  created() {
    this.fetchGames()
  },
  methods: {
    async fetchGames() {
      try {
        this.loading = true
        const response = await this.$store.dispatch('fetchGames')
        this.games = response
      } catch (error) {
        this.$store.commit('setError', '获取游戏失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    formatStatus(status) {
      const statusMap = {
        'CREATED': '已创建',
        'IN_PROGRESS': '进行中',
        'COMPLETED': '已完成'
      }
      return statusMap[status] || status
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    }
  }
}
</script>

<style scoped>
.game-list {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.game-table {
  overflow-x: auto;
}
</style> 