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
        <div class="alert alert-info">
          <h5>策略代码说明</h5>
          <p>您需要编写一个名为<code>make_move</code>的函数，该函数接收一个参数：</p>
          <ul>
            <li><code>opponent_history</code>：列表，包含对手之前的选择 ('C' 或 'D')</li>
          </ul>
          <p>函数必须返回 'C'（合作）或 'D'（背叛）。</p>
          <p>例如：</p>
          <pre class="bg-light p-2">
def make_move(opponent_history):
    """
    根据对手历史选择决定下一步行动
    
    :param opponent_history: 对手历史选择的列表，例如 ['C', 'D', 'C']
    :return: 'C' 表示合作，'D' 表示背叛
    """
    if not opponent_history:  # 第一轮
        return 'C'  # 首轮选择合作
    
    # 后续回合的策略逻辑
    if opponent_history[-1] == 'D':
        return 'D'  # 如果对手上一轮背叛，则背叛
    return 'C'  # 否则选择合作
</pre>
        </div>
        <textarea 
          class="form-control code-editor" 
          id="code" 
          v-model="strategy.code" 
          rows="15"
          required
        ></textarea>
        <small class="form-text text-muted">
          请确保您的代码包含一个名为<code>make_move</code>的函数，且该函数接受一个参数<code>opponent_history</code>。
        </small>
      </div>

      <div class="form-group mb-3">
        <button type="button" class="btn btn-outline-secondary mb-2" @click="insertTemplate">插入标准模板</button>
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
      templateCode: `def make_move(opponent_history):
    """
    根据对手历史选择决定下一步行动
    
    :param opponent_history: 对手历史选择的列表，例如 ['C', 'D', 'C']
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 在这里编写您的策略逻辑
    if not opponent_history:  # 第一轮
        return 'C'  # 首轮选择合作
    
    # 这只是一个示例策略，您可以根据需要修改
    # 以下策略为: 如果对手上一轮背叛，则背叛；否则合作
    if opponent_history[-1] == 'D':
        return 'D'
    return 'C'
`,
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
    } else {
      // 新建策略时，默认使用模板代码
      this.strategy.code = this.templateCode
    }
  },
  methods: {
    insertTemplate() {
      this.strategy.code = this.templateCode
    },
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
        
        // 检查代码是否包含make_move函数
        if (!this.strategy.code.includes('def make_move(')) {
          throw new Error('策略代码必须包含名为make_move的函数')
        }
        
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

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style> 