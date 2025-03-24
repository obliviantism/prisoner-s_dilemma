<template>
  <div class="strategy-form">
    <h1>{{ isEditing ? '编辑策略' : '创建新策略' }}</h1>
    
    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="sr-only">加载中...</span>
      </div>
    </div>
    
    <form v-else @submit.prevent="submitStrategy">
      <div class="form-group">
        <label for="name">策略名称</label>
        <input 
          type="text" 
          class="form-control" 
          id="name" 
          v-model="strategy.name" 
          required
        >
      </div>
      
      <div class="form-group">
        <label for="description">描述</label>
        <textarea 
          class="form-control" 
          id="description" 
          v-model="strategy.description" 
          rows="3"
        ></textarea>
      </div>
      
      <div class="form-group">
        <label for="code">策略代码</label>
        <textarea 
          class="form-control code-editor" 
          id="code" 
          v-model="strategy.code" 
          rows="10"
          required
        ></textarea>
        <small class="form-text text-muted">
          编写Python代码实现囚徒困境策略。函数应返回'C'（合作）或'D'（背叛）。
        </small>
      </div>
      
      <div class="form-group">
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? '保存中...' : '保存策略' }}
        </button>
        <router-link to="/strategies" class="btn btn-outline-secondary ml-2">
          取消
        </router-link>
      </div>
    </form>
  </div>
</template>

<script>
export default {
  name: 'StrategyFormView',
  data() {
    return {
      strategy: {
        name: '',
        description: '',
        code: ''
      },
      loading: false,
      saving: false
    }
  },
  computed: {
    isEditing() {
      return this.$route.params.id !== undefined
    }
  },
  created() {
    if (this.isEditing) {
      this.loadStrategy()
    }
  },
  methods: {
    async loadStrategy() {
      try {
        this.loading = true
        const strategyId = this.$route.params.id
        const response = await this.$store.dispatch('fetchStrategy', strategyId)
        this.strategy = response
      } catch (error) {
        this.$store.commit('setError', '获取策略失败: ' + error.message)
      } finally {
        this.loading = false
      }
    },
    async submitStrategy() {
      try {
        this.saving = true
        if (this.isEditing) {
          await this.$store.dispatch('updateStrategy', {
            id: this.$route.params.id,
            ...this.strategy
          })
        } else {
          await this.$store.dispatch('createStrategy', this.strategy)
        }
        this.$router.push('/strategies')
      } catch (error) {
        this.$store.commit('setError', '保存策略失败: ' + error.message)
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.strategy-form {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.code-editor {
  font-family: monospace;
}
</style> 