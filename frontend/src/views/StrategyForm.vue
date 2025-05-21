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
        
        <!-- 增强的代码编辑器 -->
        <div class="editor-container">
          <!-- 高亮显示层 -->
          <pre class="highlight-layer" v-html="highlightedCode"></pre>
          
          <!-- 实际编辑层 -->
          <textarea 
            ref="codeTextarea"
            class="code-editor" 
            v-model="strategy.code"
            @input="updateHighlight"
            @scroll="syncScroll"
            @keydown="handleKeyDown"
            spellcheck="false"
            autocomplete="off"
            autocorrect="off"
            autocapitalize="off"
            rows="15"
          ></textarea>
        </div>
        
        <small class="form-text text-muted mt-2">
          请确保您的代码包含一个名为<code>make_move</code>的函数，且该函数接受一个参数<code>opponent_history</code>。
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
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import 'highlight.js/styles/atom-one-dark.css';

// 注册Python语言
hljs.registerLanguage('python', python);

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
      highlightedCode: '',
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
  watch: {
    'strategy.code': {
      immediate: true,
      handler() {
        this.updateHighlight();
      }
    }
  },
  mounted() {
    if (this.isEditing) {
      this.loadStrategy()
    } else {
      // 新建策略时，默认使用模板代码
      this.strategy.code = this.templateCode;
    }
    
    // 初始化语法高亮
    this.updateHighlight();
  },
  methods: {
    // 更新语法高亮
    updateHighlight() {
      const code = this.strategy.code || '';
      try {
        const highlighted = hljs.highlight(code, { language: 'python' }).value;
        this.highlightedCode = highlighted;
      } catch (e) {
        console.error('高亮处理错误:', e);
        this.highlightedCode = this.escapeHtml(code);
      }
    },
    
    // 同步滚动位置
    syncScroll() {
      const textarea = this.$refs.codeTextarea;
      const highlightPre = textarea.previousElementSibling;
      highlightPre.scrollTop = textarea.scrollTop;
      highlightPre.scrollLeft = textarea.scrollLeft;
    },
    
    // 处理按键事件
    handleKeyDown(e) {
      // 处理Tab键
      if (e.key === 'Tab') {
        e.preventDefault();
        const textarea = e.target;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        
        // 插入Tab缩进（4个空格）
        const spaces = '    ';
        if (start === end) {
          // 无选择时，插入Tab
          this.strategy.code = this.strategy.code.substring(0, start) + spaces + this.strategy.code.substring(end);
          this.$nextTick(() => {
            textarea.selectionStart = textarea.selectionEnd = start + spaces.length;
          });
        } else {
          // 有选择时，缩进选中的行
          const selectedLines = this.strategy.code.substring(start, end).split('\n');
          const startLinePos = this.strategy.code.substring(0, start).lastIndexOf('\n') + 1;
          let endLinePos = end + this.strategy.code.substring(end).indexOf('\n');
          if (endLinePos === -1) endLinePos = this.strategy.code.length;
          
          // 为每行添加缩进
          const indentedText = selectedLines.map(line => spaces + line).join('\n');
          this.strategy.code = this.strategy.code.substring(0, startLinePos) + 
                            indentedText + 
                            this.strategy.code.substring(endLinePos);
          
          // 更新选择范围
          this.$nextTick(() => {
            textarea.selectionStart = startLinePos;
            textarea.selectionEnd = startLinePos + indentedText.length;
          });
        }
      } else if (e.key === 'Enter') {
        // 处理回车键，保持缩进
        e.preventDefault();
        const textarea = e.target;
        const start = textarea.selectionStart;
        
        // 获取当前行缩进
        const currentLine = this.strategy.code.substring(0, start).split('\n').pop();
        const indentMatch = currentLine.match(/^(\s*)/);
        const indent = indentMatch ? indentMatch[1] : '';
        
        // 检测是否需要额外缩进（如冒号结尾）
        const extraIndent = currentLine.trim().endsWith(':') ? '    ' : '';
        
        // 插入换行和缩进
        this.strategy.code = this.strategy.code.substring(0, start) + 
                           '\n' + indent + extraIndent + 
                           this.strategy.code.substring(textarea.selectionEnd);
        
        // 设置光标位置
        this.$nextTick(() => {
          const newPos = start + 1 + indent.length + extraIndent.length;
          textarea.selectionStart = textarea.selectionEnd = newPos;
        });
      }
      
      // 延迟更新高亮代码
      this.$nextTick(this.updateHighlight);
    },
    
    // HTML转义
    escapeHtml(unsafe) {
      return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
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
        this.saveError = `保存策略失败: ${error.message || '未知错误'}`;
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

/* 代码编辑器容器 */
.editor-container {
  position: relative;
  height: 400px;
  margin-bottom: 1rem;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* 高亮层 */
.highlight-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 10px;
  font-family: 'Fira Code', Consolas, Monaco, 'Andale Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
  overflow: auto;
  background-color: #282c34;
  color: #abb2bf;
  pointer-events: none;
  white-space: pre;
  z-index: 1;
}

/* 编辑层 */
.code-editor {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  border: 1px solid #444;
  padding: 10px;
  font-family: 'Fira Code', Consolas, Monaco, 'Andale Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
  background-color: transparent;
  color: transparent;
  caret-color: white;
  resize: none;
  z-index: 2;
  tab-size: 4;
  outline: none;
}

.code-editor:focus {
  border-color: #6495ED;
  box-shadow: 0 0 0 0.25rem rgba(100, 149, 237, 0.25);
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
