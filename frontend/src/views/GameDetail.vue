<template>
  <div class="game-detail">
    <h1>游戏详情</h1>
    
    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="sr-only">加载中...</span>
      </div>
    </div>
    
    <div v-else>
      <div class="card mb-4">
        <div class="card-header">
          <h5>游戏信息</h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <p><strong>游戏ID:</strong> {{ game.id }}</p>
              <p><strong>策略1:</strong> {{ game.strategy1 ? game.strategy1.name : '未知策略' }}</p>
              <p><strong>策略2:</strong> {{ game.strategy2 ? game.strategy2.name : '未知策略' }}</p>
            </div>
            <div class="col-md-6">
              <p><strong>状态:</strong> {{ formatStatus(game.status) }}</p>
              <p><strong>当前回合:</strong> {{ game.current_round }} / {{ game.total_rounds }}</p>
              <p><strong>创建时间:</strong> {{ formatDate(game.created_at) }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="card mb-4">
        <div class="card-header">
          <h5>得分</h5>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <div class="text-center">
                <h6>{{ game.strategy1 ? game.strategy1.name : '未知策略' }}</h6>
                <h2>{{ game.player1_score }}</h2>
              </div>
            </div>
            <div class="col-md-6">
              <div class="text-center">
                <h6>{{ game.strategy2 ? game.strategy2.name : '未知策略' }}</h6>
                <h2>{{ game.player2_score }}</h2>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="action-buttons mb-4">
        <button 
          v-if="game.status !== 'COMPLETED'" 
          class="btn btn-primary mr-2" 
          @click="playRound" 
          :disabled="processing"
        >
          {{ processing ? '处理中...' : '进行一回合' }}
        </button>
        
        <button 
          v-if="game.status !== 'COMPLETED'" 
          class="btn btn-success" 
          @click="playFullGame" 
          :disabled="processing"
        >
          {{ processing ? '处理中...' : '进行所有回合' }}
        </button>
        
        <router-link to="/games" class="btn btn-outline-secondary ml-2">
          返回游戏列表
        </router-link>
        
        <button 
          class="btn btn-danger ml-2" 
          @click="confirmDeleteGame" 
          :disabled="processing"
        >
          删除游戏
        </button>
      </div>
      
      <!-- 删除确认对话框 -->
      <div class="modal fade" id="deleteGameModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">确认删除</h5>
              <button type="button" class="btn-close" @click="closeModal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <p>您确定要删除这个游戏 #{{ game.id }} 吗？</p>
              <p>策略1: <strong>{{ game.strategy1 ? game.strategy1.name : '未知策略' }}</strong></p>
              <p>策略2: <strong>{{ game.strategy2 ? game.strategy2.name : '未知策略' }}</strong></p>
              <p class="text-danger"><strong>警告:</strong> 这将永久删除游戏记录并影响排行榜得分。此操作不可撤销。</p>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="closeModal">取消</button>
              <button type="button" class="btn btn-danger" @click="deleteGame" :disabled="deleting">
                {{ deleting ? '删除中...' : '删除游戏' }}
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header">
          <h5>回合历史</h5>
        </div>
        <div class="card-body">
          <div v-if="game.rounds && game.rounds.length > 0">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>回合</th>
                  <th>{{ game.strategy1 ? game.strategy1.name : '未知策略' }} 选择</th>
                  <th>{{ game.strategy2 ? game.strategy2.name : '未知策略' }} 选择</th>
                  <th>{{ game.strategy1 ? game.strategy1.name : '未知策略' }} 得分</th>
                  <th>{{ game.strategy2 ? game.strategy2.name : '未知策略' }} 得分</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="round in game.rounds" :key="round.round_number">
                  <td>{{ round.round_number }}</td>
                  <td>{{ formatChoice(round.player1_choice) }}</td>
                  <td>{{ formatChoice(round.player2_choice) }}</td>
                  <td>{{ round.player1_score }}</td>
                  <td>{{ round.player2_score }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="alert alert-info">
            尚未进行任何回合。使用上方的按钮开始游戏。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from 'bootstrap'

export default {
  name: 'GameDetailView',
  data() {
    return {
      game: {
        rounds: []
      },
      loading: true,
      processing: false,
      deleting: false,
      deleteModal: null
    }
  },
  created() {
    this.fetchGame()
  },
  mounted() {
    // 初始化模态框
    this.initModal()
  },
  beforeUnmount() {
    // 确保Modal在组件销毁前也被销毁
    if (this.deleteModal) {
      this.deleteModal.dispose()
      this.deleteModal = null
    }
  },
  methods: {
    async fetchGame() {
      try {
        this.loading = true
        const gameId = this.$route.params.id
        const response = await this.$store.dispatch('fetchGame', gameId)
        this.game = response
        
        // 数据加载完成后，初始化模态框
        this.initModal()
      } catch (error) {
        this.$store.commit('setError', '获取游戏失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    async playRound() {
      try {
        this.processing = true
        const gameId = this.$route.params.id
        await this.$store.dispatch('playRound', gameId)
        await this.fetchGame()
      } catch (error) {
        this.$store.commit('setError', '进行回合失败: ' + error.message)
      } finally {
        this.processing = false
      }
    },
    async playFullGame() {
      try {
        this.processing = true
        const gameId = this.$route.params.id
        await this.$store.dispatch('playFullGame', gameId)
        await this.fetchGame()
      } catch (error) {
        this.$store.commit('setError', '进行游戏失败: ' + error.message)
      } finally {
        this.processing = false
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
    formatChoice(choice) {
      if (choice === 'C') return '合作'
      if (choice === 'D') return '背叛'
      return choice
    },
    initModal() {
      this.$nextTick(() => {
        if (!this.deleteModal) {
          const modalElement = document.getElementById('deleteGameModal')
          if (modalElement) {
            try {
              this.deleteModal = new Modal(modalElement)
            } catch (error) {
              console.error('初始化Modal失败:', error)
            }
          }
        }
      })
    },
    closeModal() {
      if (this.deleteModal) {
        try {
          this.deleteModal.hide()
        } catch (error) {
          console.error('关闭Modal失败:', error)
        }
      }
    },
    confirmDeleteGame() {
      this.initModal() // 确保Modal已初始化
      
      // 等待下一个DOM更新周期，确保Modal已就绪
      this.$nextTick(() => {
        if (this.deleteModal) {
          try {
            this.deleteModal.show()
          } catch (error) {
            console.error('显示Modal失败:', error)
            alert('确认删除: 您确定要删除这个游戏吗？') // 备用确认方式
          }
        } else {
          alert('确认删除: 您确定要删除这个游戏吗？') // 备用确认方式
        }
      })
    },
    async deleteGame() {
      try {
        this.deleting = true
        const gameId = this.$route.params.id
        await this.$store.dispatch('deleteGame', gameId)
        
        // 删除成功后返回游戏列表页面 - 跳转前不再尝试处理modal
        // 而是直接使用强制清理的方式处理模态框痕迹
        document.body.classList.remove('modal-open')
        const backdrop = document.querySelector('.modal-backdrop')
        if (backdrop) backdrop.parentNode.removeChild(backdrop)
        
        // 直接销毁模态框，不再调用hide方法
        if (this.deleteModal) {
          try {
            this.deleteModal.dispose()
          } catch (e) {
            console.error('销毁模态框失败', e)
          }
          this.deleteModal = null
        }
        
        // 延迟跳转，确保DOM操作完成
        setTimeout(() => {
          this.$router.push('/games')
        }, 50)
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
.game-detail {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}
</style> 