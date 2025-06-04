<template>
  <div class="strategy-list">
    <h1>我的策略</h1>
    <div class="action-buttons mb-4">
      <router-link to="/strategies/create" class="btn btn-primary me-2">
        创建新策略
      </router-link>
      <button class="btn btn-success" @click="showPresetModalDialog">
        添加预设策略
      </button>
    </div>

    <div v-if="loading" class="text-center">
      <loading-spinner text="策略加载中..." />
    </div>

    <div v-else-if="strategies.length === 0" class="alert alert-info">
      您还没有创建任何策略。点击上方的"创建新策略"按钮开始，或者使用"添加预设策略"快速添加常用策略。
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

    <!-- 预设策略对话框 -->
    <div class="modal fade" id="presetStrategyModal" tabindex="-1" ref="presetStrategyModal"
         aria-labelledby="presetStrategyModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="presetStrategyModalLabel">添加预设策略</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p>选择要添加的预设策略：</p>
            
            <div v-if="addingPresets" class="text-center my-4">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">添加中...</span>
              </div>
              <p class="mt-2">正在添加预设策略，请稍候...</p>
              <div class="progress">
                <div class="progress-bar" :style="{ width: progressPercentage + '%' }">
                  {{ addedCount }}/{{ selectedPresets.length }}
                </div>
              </div>
            </div>
            
            <div v-else>
              <div class="mb-3">
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" id="selectAll" 
                         :checked="selectedPresets.length === availablePresets.length"
                         @change="toggleSelectAll">
                  <label class="form-check-label" for="selectAll">
                    <strong>全选/取消全选</strong>
                  </label>
                </div>
              </div>

              <div v-if="availablePresets.length === 0" class="alert alert-info">
                您已添加所有预设策略，无法再次添加相同的策略。
              </div>

              <div v-else class="table-responsive">
                <table class="table table-hover">
                  <thead>
                    <tr>
                      <th style="width: 50px;"></th>
                      <th>策略名称</th>
                      <th>描述</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(preset, index) in availablePresets" :key="index">
                      <td>
                        <div class="form-check">
                          <input class="form-check-input" type="checkbox" 
                                :id="'preset-' + index"
                                v-model="selectedPresets"
                                :value="index">
                        </div>
                      </td>
                      <td><strong>{{ preset.name }}</strong></td>
                      <td>{{ preset.description }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" :disabled="addingPresets">
              取消
            </button>
            <button type="button" class="btn btn-primary" @click="addSelectedPresets" 
                    :disabled="selectedPresets.length === 0 || addingPresets">
              添加选中的策略
            </button>
            <button type="button" class="btn btn-success" @click="addAllPresets" 
                    :disabled="addingPresets">
              一键添加全部
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import LoadingSpinner from '../components/LoadingSpinner.vue';
import { Modal } from 'bootstrap';

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
      deleting: false,
      showPresetModal: false,
      selectedPresets: [],
      addingPresets: false,
      addedCount: 0,
      presetModal: null,
      availablePresets: [],
      presetStrategies: [
        {
          name: "始终合作 (Always Cooperate)",
          description: "无论对手采取什么行动，该策略都始终选择合作。",
          code: `def make_move(opponent_history):
    """
    始终合作策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作
    """
    return 'C'  # 始终选择合作
`
        },
        {
          name: "始终背叛 (Always Defect)",
          description: "无论对手采取什么行动，该策略都始终选择背叛。",
          code: `def make_move(opponent_history):
    """
    始终背叛策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'D' 表示背叛
    """
    return 'D'  # 始终选择背叛
`
        },
        {
          name: "针锋相对 (Tit for Tat)",
          description: "第一回合选择合作，随后模仿对手上一回合的选择。这是一种简单但非常有效的策略。",
          code: `def make_move(opponent_history):
    """
    针锋相对策略 (Tit for Tat)
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    if not opponent_history:  # 第一轮
        return 'C'  # 首轮选择合作
    
    # 模仿对手上一轮的选择
    return opponent_history[-1]
`
        },
        {
          name: "宽容版针锋相对 (Tit for Two Tats)",
          description: "只有当对手连续两次背叛时才选择背叛，其他情况选择合作。比标准的针锋相对更宽容。",
          code: `def make_move(opponent_history):
    """
    宽容版针锋相对策略 (Tit for Two Tats)
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    if len(opponent_history) < 2:  # 前两轮
        return 'C'  # 选择合作
    
    # 只有当对手连续两次背叛时才背叛
    if opponent_history[-1] == 'D' and opponent_history[-2] == 'D':
        return 'D'
    return 'C'
`
        },
        {
          name: "随机策略 (Random)",
          description: "随机选择合作或背叛，各50%的概率。",
          code: `import random

def make_move(opponent_history):
    """
    随机策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 随机返回 'C' 或 'D'，各50%的概率
    return random.choice(['C', 'D'])
`
        },
        {
          name: "怀疑者 (Suspicious Tit for Tat)",
          description: "第一回合选择背叛，随后模仿对手上一回合的选择。是针锋相对的一个变种。",
          code: `def make_move(opponent_history):
    """
    怀疑者策略 (Suspicious Tit for Tat)
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    if not opponent_history:  # 第一轮
        return 'D'  # 首轮选择背叛
    
    # 模仿对手上一轮的选择
    return opponent_history[-1]
`
        },
        {
          name: "grudger (永不原谅)",
          description: "开始时选择合作，但如果对手曾经背叛过，则永远选择背叛。",
          code: `def make_move(opponent_history):
    """
    永不原谅策略 (Grudger)
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    if not opponent_history:  # 第一轮
        return 'C'  # 首轮选择合作
    
    # 如果对手曾经背叛过，永远选择背叛
    if 'D' in opponent_history:
        return 'D'
    return 'C'
`
        },
        {
          name: "pavlov (胜者为王)",
          description: "如果上一回合双方选择相同（都合作或都背叛），则这一回合选择合作；否则选择背叛。",
          code: `def make_move(opponent_history):
    """
    胜者为王策略 (Pavlov)
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    if not opponent_history:  # 第一轮
        return 'C'  # 首轮选择合作
    
    # 获取自己上一轮的选择
    my_last_move = get_my_last_move(opponent_history)
    
    # 如果双方选择相同，选择合作；否则选择背叛
    if my_last_move == opponent_history[-1]:
        return 'C'
    return 'D'

def get_my_last_move(opponent_history):
    """
    根据对手历史推断自己上一轮的选择
    这是一个简化版，假设我们遵循Pavlov策略
    """
    if len(opponent_history) == 1:
        return 'C'  # 假设第一轮我们选择了合作
    
    # 递归确定上一轮的选择
    prev_my_move = get_my_last_move(opponent_history[:-1])
    
    if prev_my_move == opponent_history[-2]:
        return 'C'
    return 'D'
`
        }
      ]
    }
  },
  computed: {
    progressPercentage() {
      if (this.selectedPresets.length === 0) return 0;
      return (this.addedCount / this.selectedPresets.length) * 100;
    }
  },
  created() {
    this.fetchStrategies()
  },
  mounted() {
    // 初始化Bootstrap模态框
    this.$nextTick(() => {
      if (this.$refs.presetStrategyModal) {
        // 使用全局Bootstrap实例
        if (window.bootstrap) {
          this.presetModal = new window.bootstrap.Modal(this.$refs.presetStrategyModal);
        } else {
          // 如果全局实例不可用，则使用导入的Modal
          this.presetModal = new Modal(this.$refs.presetStrategyModal);
        }
      }
    });
  },
  beforeUnmount() {
    // 清理Bootstrap模态框
    if (this.presetModal) {
      this.presetModal.dispose();
    }
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
    },
    toggleSelectAll(event) {
      if (event.target.checked) {
        // 全选
        this.selectedPresets = this.availablePresets.map((_, index) => index);
      } else {
        // 取消全选
        this.selectedPresets = [];
      }
    },
    closePresetModal() {
      if (this.addingPresets) return;
      if (this.presetModal) {
        this.presetModal.hide();
      }
      this.selectedPresets = [];
    },
    addAllPresets() {
      this.selectedPresets = this.availablePresets.map((_, index) => index);
      this.addSelectedPresets();
    },
    async addSelectedPresets() {
      if (this.selectedPresets.length === 0) return;
      
      this.addingPresets = true;
      this.addedCount = 0;
      
      try {
        // 创建选中的预设策略
        for (const index of this.selectedPresets) {
          const preset = this.availablePresets[index];
          await this.$store.dispatch('createStrategy', {
            name: preset.name,
            description: preset.description,
            code: preset.code
          });
          this.addedCount++;
        }
        
        // 刷新策略列表
        await this.fetchStrategies();
        
        // 关闭模态框
        if (this.presetModal) {
          this.presetModal.hide();
        }
        this.selectedPresets = [];
        
        // 显示成功消息
        this.$emit('alert', `成功添加了 ${this.addedCount} 个预设策略`, 'success');
      } catch (error) {
        console.error('添加预设策略失败:', error);
        this.$store.commit('setError', '添加预设策略失败: ' + error.message);
      } finally {
        this.addingPresets = false;
      }
    },
    showPresetModalDialog() {
      this.selectedPresets = [];
      
      // 过滤掉已经添加过的预设策略
      const hasAvailable = this.filterExistingPresets();
      
      // 如果没有可用的预设策略，不显示模态框
      if (!hasAvailable) {
        return;
      }
      
      if (this.presetModal) {
        this.presetModal.show();
      } else {
        this.$nextTick(() => {
          if (this.$refs.presetStrategyModal) {
            if (window.bootstrap) {
              this.presetModal = new window.bootstrap.Modal(this.$refs.presetStrategyModal);
            } else {
              this.presetModal = new Modal(this.$refs.presetStrategyModal);
            }
            this.presetModal.show();
          } else {
            console.error('Modal element not found');
          }
        });
      }
    },
    
    // 过滤掉已经添加过的预设策略
    filterExistingPresets() {
      // 获取已有策略的名称集合
      const existingNames = new Set(this.strategies.map(s => s.name));
      
      // 过滤可用的预设策略
      this.availablePresets = this.presetStrategies.filter(preset => 
        !existingNames.has(preset.name)
      );
      
      // 如果没有可用的预设策略，显示提示信息
      if (this.availablePresets.length === 0) {
        this.$emit('alert', '您已添加所有预设策略，无法再次添加', 'info');
        return false;
      }
      
      return true;
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

.progress {
  height: 20px;
  margin-top: 10px;
}

@media (min-width: 768px) {
  .strategy-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style> 