<template>
  <div class="leaderboard">
    <h1>策略排行榜</h1>
    
    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="sr-only">加载中...</span>
      </div>
    </div>
    
    <div v-else-if="strategies.length === 0" class="alert alert-info">
      目前没有任何策略数据。请先创建策略并进行一些游戏。
    </div>
    
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h5>策略得分排名（按平均得分）</h5>
        </div>
        <div class="card-body">
          <table class="table table-striped">
            <thead>
              <tr>
                <th>排名</th>
                <th>策略名称</th>
                <th>创建者</th>
                <th>游戏数</th>
                <th>总得分</th>
                <th>平均得分</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(strategy, index) in strategies" :key="strategy.strategy_id">
                <td>{{ index + 1 }}</td>
                <td>{{ strategy.strategy_name }}</td>
                <td>{{ strategy.created_by }}</td>
                <td>{{ strategy.total_games }}</td>
                <td>{{ strategy.total_score }}</td>
                <td>{{ strategy.avg_score.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <div class="mt-4">
        <p class="text-muted">
          <small>说明：排行榜基于所有已完成的游戏。平均得分是该策略在所有参与的游戏中的平均得分。</small>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LeaderboardView',
  data() {
    return {
      strategies: [],
      loading: true
    }
  },
  created() {
    this.fetchLeaderboard()
  },
  methods: {
    async fetchLeaderboard() {
      try {
        this.loading = true
        const response = await this.$store.dispatch('fetchLeaderboard')
        this.strategies = response
      } catch (error) {
        this.$store.commit('setError', '获取排行榜失败: ' + error.message)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.leaderboard {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}
</style> 