<template>
  <div class="strategy-list">
    <h1>我的策略</h1>
    <div class="action-buttons mb-4">
      <router-link to="/strategies/create" class="btn btn-primary">
        创建新策略
      </router-link>
    </div>

    <div v-if="loading" class="text-center">
      <loading-spinner text="策略加载中..." />
    </div>

    <div v-else-if="strategies.length === 0" class="alert alert-info">
      您还没有创建任何策略。点击上方的"创建新策略"按钮开始。
    </div>

    <div v-else class="strategy-cards">
      <div v-for="strategy in strategies" :key="strategy.id" class="card mb-3">
        <div class="card-body">
          <h5 class="card-title">{{ strategy.name }}</h5>
          <p class="card-text">{{ strategy.description }}</p>
          <div class="card-actions">
            <router-link :to="`/strategies/${strategy.id}/edit`" class="btn btn-sm btn-outline-primary me-2">
              编辑
            </router-link>
            <button @click="confirmDelete(strategy)" class="btn btn-sm btn-outline-danger">
              删除
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 确认删除对话框 -->
    <div v-if="showDeleteConfirm" class="modal fade show" tabindex="-1" 
         style="display: block; background-color: rgba(0,0,0,0.5);">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">确认删除</h5>
            <button type="button" class="btn-close" @click="cancelDelete"></button>
          </div>
          <div class="modal-body">
            <p>您确定要删除策略 "{{ strategyToDelete ? strategyToDelete.name : '' }}" 吗？</p>
            <p class="text-danger">此操作不可逆，所有关联的游戏记录将保持不变。</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="cancelDelete">取消</button>
            <button type="button" class="btn btn-danger" @click="deleteStrategy" :disabled="deleting">
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import LoadingSpinner from '../components/LoadingSpinner.vue';

export default {
  name: 'StrategyListView',
  components: {
    LoadingSpinner
  },
  data() {
    return {
      strategies: [],
      loading: true,
      showDeleteConfirm: false,
      strategyToDelete: null,
      deleting: false
    }
  },
  created() {
    this.fetchStrategies()
  },
  methods: {
    async fetchStrategies() {
      try {
        this.loading = true
        const response = await this.$store.dispatch('fetchStrategies')
        this.strategies = response
      } catch (error) {
        this.$store.commit('setError', '获取策略失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    confirmDelete(strategy) {
      this.strategyToDelete = strategy
      this.showDeleteConfirm = true
    },
    cancelDelete() {
      this.showDeleteConfirm = false
      this.strategyToDelete = null
    },
    async deleteStrategy() {
      if (!this.strategyToDelete) return
      
      try {
        this.deleting = true
        await this.$store.dispatch('deleteStrategy', this.strategyToDelete.id)
        // 刷新策略列表
        await this.fetchStrategies()
        this.showDeleteConfirm = false
        this.strategyToDelete = null
      } catch (error) {
        this.$store.commit('setError', '删除策略失败: ' + error.message)
      } finally {
        this.deleting = false
      }
    }
  }
}
</script>

<style scoped>
.strategy-list {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.strategy-cards {
  display: grid;
  gap: 20px;
}

.card-actions {
  display: flex;
  justify-content: flex-start;
  margin-top: 10px;
}

@media (min-width: 768px) {
  .strategy-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style> 