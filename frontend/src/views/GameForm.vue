<template>
  <div class="game-form">
    <h1>创建新游戏</h1>
    
    <div v-if="loadingStrategies" class="text-center">
      <div class="spinner-border" role="status">
        <span class="sr-only">加载中...</span>
      </div>
    </div>
    
    <form v-else @submit.prevent="createGame">
      <div class="form-group mb-3">
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
      
      <div class="form-group mb-3">
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
      
      <div class="form-group mb-3">
        <label>回合数量选项</label>
        <div class="form-check mb-2">
          <input 
            class="form-check-input" 
            type="radio" 
            id="fixedRounds" 
            value="fixed" 
            v-model="roundsOption"
          >
          <label class="form-check-label" for="fixedRounds">
            指定回合数
          </label>
        </div>
        
        <div class="form-check mb-2">
          <input 
            class="form-check-input" 
            type="radio" 
            id="randomRounds" 
            value="random" 
            v-model="roundsOption"
          >
          <label class="form-check-label" for="randomRounds">
            随机回合数
          </label>
        </div>
      </div>
      
      <div v-if="roundsOption === 'fixed'" class="form-group mb-3">
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
      
      <div v-else class="form-group mb-3">
        <label>随机回合范围</label>
        <div class="row">
          <div class="col">
            <label for="minRounds">最小回合数</label>
            <input 
              type="number" 
              class="form-control" 
              id="minRounds" 
              v-model.number="formData.minRounds" 
              min="1" 
              max="999"
              required
            >
          </div>
          <div class="col">
            <label for="maxRounds">最大回合数</label>
            <input 
              type="number" 
              class="form-control" 
              id="maxRounds" 
              v-model.number="formData.maxRounds" 
              min="2" 
              max="1000"
              required
            >
          </div>
        </div>
        <div v-if="rangeError" class="text-danger mt-2">
          {{ rangeError }}
        </div>
      </div>
      
      <div class="form-group">
        <button type="submit" class="btn btn-primary" :disabled="creating || !!rangeError">
          {{ creating ? '创建中...' : '创建游戏' }}
        </button>
        <router-link to="/games" class="btn btn-outline-secondary ms-2">
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
      roundsOption: 'fixed', // 默认使用固定回合数
      formData: {
        strategy1: '',
        strategy2: '',
        totalRounds: 200,
        minRounds: 50,
        maxRounds: 200
      },
      creating: false
    }
  },
  computed: {
    rangeError() {
      if (this.roundsOption === 'random') {
        if (this.formData.minRounds >= this.formData.maxRounds) {
          return '最小回合数必须小于最大回合数';
        }
        if (this.formData.maxRounds - this.formData.minRounds < 10) {
          return '最大回合数和最小回合数之差应至少为10';
        }
      }
      return null;
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
    generateRandomRounds() {
      const min = this.formData.minRounds;
      const max = this.formData.maxRounds;
      return Math.floor(Math.random() * (max - min + 1)) + min;
    },
    async createGame() {
      // 如果选择随机回合数，生成一个随机数
      const totalRounds = this.roundsOption === 'random' 
        ? this.generateRandomRounds() 
        : this.formData.totalRounds;
      
      try {
        this.creating = true
        await this.$store.dispatch('createGame', {
          strategy1: this.formData.strategy1,
          strategy2: this.formData.strategy2,
          total_rounds: totalRounds
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