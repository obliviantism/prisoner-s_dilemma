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
            <router-link :to="`/strategies/${strategy.id}/edit`" class="btn btn-sm btn-outline-primary mr-2">
              编辑
            </router-link>
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
      loading: true
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

@media (min-width: 768px) {
  .strategy-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style> 