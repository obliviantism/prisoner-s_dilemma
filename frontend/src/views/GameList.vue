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
              <button 
                class="btn btn-sm btn-outline-danger ms-1" 
                @click="confirmDeleteGame(game)"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 删除确认对话框 -->
    <div class="modal fade" id="deleteGameModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">确认删除</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body" v-if="gameToDelete">
            <p>您确定要删除这个游戏 #{{ gameToDelete.id }} 吗？</p>
            <p>策略1: <strong>{{ gameToDelete.strategy1 ? gameToDelete.strategy1.name : '未知策略' }}</strong></p>
            <p>策略2: <strong>{{ gameToDelete.strategy2 ? gameToDelete.strategy2.name : '未知策略' }}</strong></p>
            <p class="text-danger"><strong>警告:</strong> 这将永久删除游戏记录并影响排行榜得分。此操作不可撤销。</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-danger" @click="deleteGame" :disabled="deleting">
              {{ deleting ? '删除中...' : '删除游戏' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as bootstrap from 'bootstrap'

export default {
  name: 'GameListView',
  data() {
    return {
      games: [],
      loading: true,
      gameToDelete: null,
      deleting: false
    }
  },
  created() {
    this.fetchGames()
  },
  mounted() {
    // 初始化Bootstrap Modal
    this.deleteModal = new bootstrap.Modal(document.getElementById('deleteGameModal'))
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
    },
    confirmDeleteGame(game) {
      this.gameToDelete = game
      this.deleteModal.show()
    },
    async deleteGame() {
      try {
        this.deleting = true
        await this.$store.dispatch('deleteGame', this.gameToDelete.id)
        this.games = this.games.filter(g => g.id !== this.gameToDelete.id)
        this.deleteModal.hide()
        this.gameToDelete = null
      } catch (error) {
        this.$store.commit('setError', '删除游戏失败: ' + error.message)
      } finally {
        this.deleting = false
      }
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