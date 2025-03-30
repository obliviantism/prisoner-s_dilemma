<template>
  <div class="strategy-form">
    <h1>{{ isEditing ? '编辑策略' : '创建新策略' }}</h1>
    
    <div v-if="loading" class="text-center">
      <div class="spinner-border" role="status">
        <span class="sr-only">加载中...</span>
      </div>
    </div>
    
    <div v-else-if="loadError" class="alert alert-danger">
      {{ loadError }}
      <div class="mt-3">
        <router-link to="/strategies" class="btn btn-primary">返回策略列表</router-link>
      </div>
    </div>
    
    <form v-else @submit.prevent="submitStrategy">
      <div class="form-group mb-3">
        <label for="name">策略名称</label>
        <input 
          type="text" 
          class="form-control" 
          id="name" 
          v-model="strategy.name" 
          required
        >
      </div>
      
      <div class="form-group mb-3">
        <label for="description">描述</label>
        <textarea 
          class="form-control" 
          id="description" 
          v-model="strategy.description" 
          rows="3"
        ></textarea>
      </div>
      
      <div class="form-group mb-3">
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
      
      <div v-if="saveError" class="alert alert-danger mb-3">
        {{ saveError }}
      </div>
      
      <div class="form-group">
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? '保存中...' : '保存策略' }}
        </button>
        <router-link to="/strategies" class="btn btn-outline-secondary ms-2">
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
      saving: false,
      loadError: null,
      saveError: null
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
        this.loadError = null
        
        const strategyId = this.$route.params.id
        const data = await this.$store.dispatch('fetchStrategy', strategyId)
        
        if (!data || !data.name) {
          throw new Error('获取到的策略数据无效')
        }
        
        this.strategy = {
          name: data.name || '',
          description: data.description || '',
          code: data.code || ''
        }
      } catch (error) {
        console.error('加载策略失败:', error)
        this.loadError = `获取策略失败: ${error.message || '未知错误'}`
        this.$store.commit('setError', this.loadError)
      } finally {
        this.loading = false
      }
    },
    async submitStrategy() {
      try {
        this.saving = true
        this.saveError = null
        
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
        console.error('保存策略失败:', error)
        this.saveError = `保存策略失败: ${error.message || '未知错误'}`
        this.$store.commit('setError', this.saveError)
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