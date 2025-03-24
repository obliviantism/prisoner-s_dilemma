<template>
  <div class="game-form">
    <h1>创建新游戏</h1>
    
    <div v-if="loadingStrategies" class="text-center">
      <div class="spinner-border" role="status">
        <span class="sr-only">加载中...</span>
      </div>
    </div>
    
    <form v-else @submit.prevent="createGame">
      <div class="form-group">
        <label for="strategy1">策略1</label>
        <select 
          class="form-control" 
          id="strategy1" 
          v-model="formData.strategy1" 
          required
        >
          <option value="" disabled>选择策略1</option>
          <option 
            v-for="strategy in strategies" 
            :key="strategy.id" 
            :value="strategy.id"
          >
            {{ strategy.name }}
          </option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="strategy2">策略2</label>
        <select 
          class="form-control" 
          id="strategy2" 
          v-model="formData.strategy2" 
          required
        >
          <option value="" disabled>选择策略2</option>
          <option 
            v-for="strategy in strategies" 
            :key="strategy.id" 
            :value="strategy.id"
          >
            {{ strategy.name }}
          </option>
        </select>
      </div>
      
      <div class="form-group">
        <label for="rounds">回合数量</label>
        <input 
          type="number" 
          class="form-control" 
          id="rounds" 
          v-model.number="formData.totalRounds" 
          min="1" 
          max="1000"
          required
        >
      </div>
      
      <div class="form-group">
        <button type="submit" class="btn btn-primary" :disabled="creating">
          {{ creating ? '创建中...' : '创建游戏' }}
        </button>
        <router-link to="/games" class="btn btn-outline-secondary ml-2">
          取消
        </router-link>
      </div>
    </form>
  </div>
</template>

<script>
export default {
  name: 'GameFormView',
  data() {
    return {
      strategies: [],
      loadingStrategies: true,
      formData: {
        strategy1: '',
        strategy2: '',
        totalRounds: 200
      },
      creating: false
    }
  },
  created() {
    this.fetchStrategies()
  },
  methods: {
    async fetchStrategies() {
      try {
        this.loadingStrategies = true
        const response = await this.$store.dispatch('fetchStrategies')
        this.strategies = response
      } catch (error) {
        this.$store.commit('setError', '获取策略失败: ' + error.message)
      } finally {
        this.loadingStrategies = false
      }
    },
    async createGame() {
      if (this.formData.strategy1 === this.formData.strategy2) {
        this.$store.commit('setError', '策略1和策略2不能相同')
        return
      }
      
      try {
        this.creating = true
        await this.$store.dispatch('createGame', {
          strategy1: this.formData.strategy1,
          strategy2: this.formData.strategy2,
          total_rounds: this.formData.totalRounds
        })
        this.$router.push('/games')
      } catch (error) {
        this.$store.commit('setError', '创建游戏失败: ' + error.message)
      } finally {
        this.creating = false
      }
    }
  }
}
</script>

<style scoped>
.game-form {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}
</style> 