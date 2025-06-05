<template>
  <div class="strategy-list">
    <h1>我的策略</h1>
    <div class="action-buttons mb-4">
      <router-link to="/strategies/create" class="btn btn-primary me-2">
        创建新策略
      </router-link>
      <button class="btn btn-success me-2" @click="showPresetModalDialog">
        添加预设策略
      </button>
      <button class="btn btn-info" @click="showDeletedPresetModalDialog">
        恢复已删除预设策略
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

    <!-- 已删除预设策略模态框 -->
    <div class="modal fade" id="deletedPresetStrategyModal" tabindex="-1" ref="deletedPresetStrategyModal"
         aria-labelledby="deletedPresetStrategyModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="deletedPresetStrategyModalLabel">恢复已删除的预设策略</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="loadingDeletedPresets" class="text-center">
              <loading-spinner text="加载中..." />
            </div>
            <div v-else-if="deletedPresets.length === 0" class="alert alert-info">
              没有找到已删除的预设策略。您可能尚未删除任何预设策略，或者已经全部恢复。
            </div>
            <div v-else>
              <p>以下是您曾经添加但已删除的预设策略：</p>
              
              <div v-if="addingPresets" class="text-center my-4">
                <div class="spinner-border" role="status">
                  <span class="visually-hidden">添加中...</span>
                </div>
                <p class="mt-2">正在恢复预设策略，请稍候...</p>
                <div class="progress">
                  <div class="progress-bar" :style="{ width: progressPercentage + '%' }">
                    {{ addedCount }}/{{ selectedPresets.length }}
                  </div>
                </div>
              </div>
              
              <div v-else>
                <div class="mb-3">
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" id="selectAllDeleted" 
                           :checked="selectedPresets.length === deletedPresets.length"
                           @change="toggleSelectAllDeleted">
                    <label class="form-check-label" for="selectAllDeleted">
                      <strong>全选/取消全选</strong>
                    </label>
                  </div>
                </div>

                <div class="table-responsive">
                  <table class="table table-hover">
                    <thead>
                      <tr>
                        <th style="width: 50px;"></th>
                        <th>策略名称</th>
                        <th>描述</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(preset, index) in deletedPresets" :key="index">
                        <td>
                          <div class="form-check">
                            <input class="form-check-input" type="checkbox" 
                                  :id="'deleted-preset-' + index"
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
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" :disabled="addingPresets">
              取消
            </button>
            <button type="button" class="btn btn-primary" @click="addSelectedDeletedPresets" 
                    :disabled="selectedPresets.length === 0 || addingPresets">
              恢复选中的策略
            </button>
            <button type="button" class="btn btn-success" @click="addAllDeletedPresets" 
                    :disabled="deletedPresets.length === 0 || addingPresets">
              一键恢复全部
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
import axios from 'axios';

export default {
  name: 'StrategyList',
  components: {
    LoadingSpinner
  },
  data() {
    return {
      strategies: [],
      loading: false,
      showDeleteConfirm: false,
      strategyToDelete: null,
      deleting: false,
      showPresetModal: false,
      selectedPresets: [],
      availablePresets: [],
      deletedPresets: [],
      loadingDeletedPresets: false,
      addingPresets: false,
      presetModal: null,
      deletedPresetModal: null,
      addedCount: 0
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
    this.fetchPresetStrategies()
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
      
      if (this.$refs.deletedPresetStrategyModal) {
        if (window.bootstrap) {
          this.deletedPresetModal = new window.bootstrap.Modal(this.$refs.deletedPresetStrategyModal);
        } else {
          this.deletedPresetModal = new Modal(this.$refs.deletedPresetStrategyModal);
        }
      }
    });
  },
  beforeUnmount() {
    // 清理Bootstrap模态框
    if (this.presetModal) {
      this.presetModal.dispose();
    }
    if (this.deletedPresetModal) {
      this.deletedPresetModal.dispose();
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
    async fetchPresetStrategies() {
      try {
        // 从API获取预设策略列表
        const response = await this.$store.dispatch('fetchPresetStrategies')
        this.availablePresets = response
        
        // 过滤掉已经添加的策略
        this.filterExistingPresets()
      } catch (error) {
        console.error('获取预设策略失败:', error)
        this.$store.commit('setError', '获取预设策略失败: ' + error.message)
      }
    },
    filterExistingPresets() {
      // 记录一下当前已有策略
      console.log('当前所有策略:', this.strategies);
      
      // 获取当前已有策略的preset_id列表
      const existingPresetIds = this.strategies
        .filter(s => s.is_preset) // 只选择是预设策略的
        .map(s => s.preset_id);   // 获取预设ID
      
      console.log('现有预设策略IDs:', existingPresetIds);
      
      // 不再过滤掉已经添加的预设策略，允许重复添加
      // this.availablePresets = this.availablePresets.filter(preset => {
      //   // 如果该预设ID不在现有预设策略中，则允许添加
      //   return !existingPresetIds.includes(preset.id);
      // });
      
      console.log('可添加的预设策略:', this.availablePresets.length);
      
      // 如果没有可用的预设策略，返回false
      if (this.availablePresets.length === 0) {
        this.$emit('alert', '没有找到可用的预设策略', 'info');
        return false;
      }
      
      return true;
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
        console.log(`开始删除策略: ${this.strategyToDelete.name} (ID: ${this.strategyToDelete.id})`)
        
        await this.$store.dispatch('deleteStrategy', this.strategyToDelete.id)
        
        // 删除成功，显示成功消息
        this.$emit('alert', `策略 "${this.strategyToDelete.name}" 已成功删除`, 'success')
        
        // 刷新策略列表
        await this.fetchStrategies()
        this.showDeleteConfirm = false
        this.strategyToDelete = null
      } catch (error) {
        console.error('删除策略失败:', error)
        
        // 提供更具体的错误消息
        let errorMessage = '删除策略失败'
        
        if (error.response) {
          // 服务器返回的错误
          if (error.response.status === 403) {
            errorMessage = '没有权限删除此策略'
          } else if (error.response.status === 404) {
            errorMessage = '策略不存在或已被删除'
          } else if (error.response.status === 409 || error.response.status === 500) {
            // 冲突或服务器错误 - 可能是外键约束
            errorMessage = '无法删除此策略，因为它正在被游戏或锦标赛使用'
          } else if (error.response.data && error.response.data.error) {
            // 服务器返回的具体错误消息
            errorMessage = error.response.data.error
          }
        }
        
        // 显示错误消息
        this.$emit('alert', errorMessage, 'danger')
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
        // 创建选中的预设策略，逐个添加并添加更多的错误日志
        for (const index of this.selectedPresets) {
          try {
            const preset = this.availablePresets[index];
            
            // 生成唯一名称
            const timestamp = new Date().getTime();
            const strategyName = `${preset.name}-${timestamp}`;
            
            console.log(`尝试添加策略: ${strategyName}`, {
              name: strategyName,
              description: preset.description,
              code_length: preset.code ? preset.code.length : 0,
              preset_id: preset.id
            });
            
            // 创建一个精简版的策略，只包含必要字段
            const strategyData = {
              name: strategyName,
              description: preset.description || '预设策略',
              code: preset.code,
              preset_id: preset.id
            };
            
            // 使用axios直接发送请求，而不是通过Vuex
            const token = localStorage.getItem('token');
            const response = await axios.post('http://localhost:8000/api/strategies/', strategyData, {
              headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json'
              }
            });
            
            console.log(`成功添加策略: ${strategyName}`, response.data);
            this.addedCount++;
            
            // 添加短暂延迟，避免服务器压力
            await new Promise(resolve => setTimeout(resolve, 300));
          } catch (err) {
            console.error('添加策略错误:', err);
            console.error('错误详情:', {
              message: err.message,
              status: err.response?.status,
              data: err.response?.data
            });
            
            // 继续添加其他策略
            continue;
          }
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
        console.error('添加预设策略过程中发生错误:', error);
        this.$emit('alert', '添加预设策略失败: ' + (error.message || '未知错误'), 'danger');
      } finally {
        this.addingPresets = false;
        this.addedCount = 0;
        
        // 重新获取可用的预设策略
        await this.fetchPresetStrategies();
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
    async fetchDeletedPresetStrategies() {
      try {
        this.loadingDeletedPresets = true;
        this.deletedPresets = await this.$store.dispatch('fetchDeletedPresetStrategies');
        console.log('已删除的预设策略:', this.deletedPresets);
      } catch (error) {
        console.error('获取已删除的预设策略失败:', error);
        this.$emit('alert', '获取已删除的预设策略失败: ' + error.message, 'danger');
      } finally {
        this.loadingDeletedPresets = false;
      }
    },
    toggleSelectAllDeleted(event) {
      if (event.target.checked) {
        // 全选
        this.selectedPresets = this.deletedPresets.map((_, index) => index);
      } else {
        // 取消全选
        this.selectedPresets = [];
      }
    },
    showDeletedPresetModalDialog() {
      this.selectedPresets = [];
      this.fetchDeletedPresetStrategies().then(() => {
        if (this.deletedPresets.length === 0) {
          this.$emit('alert', '没有找到已删除的预设策略', 'info');
          return;
        }
        
        if (this.deletedPresetModal) {
          this.deletedPresetModal.show();
        } else {
          this.$nextTick(() => {
            if (this.$refs.deletedPresetStrategyModal) {
              if (window.bootstrap) {
                this.deletedPresetModal = new window.bootstrap.Modal(this.$refs.deletedPresetStrategyModal);
              } else {
                this.deletedPresetModal = new Modal(this.$refs.deletedPresetStrategyModal);
              }
              this.deletedPresetModal.show();
            } else {
              console.error('Deleted Preset Modal element not found');
            }
          });
        }
      });
    },
    addAllDeletedPresets() {
      this.selectedPresets = this.deletedPresets.map((_, index) => index);
      this.addSelectedDeletedPresets();
    },
    async addSelectedDeletedPresets() {
      if (this.selectedPresets.length === 0) return;
      
      this.addingPresets = true;
      this.addedCount = 0;
      
      try {
        // 创建选中的预设策略，逐个添加并添加更多的错误日志
        for (const index of this.selectedPresets) {
          try {
            const preset = this.deletedPresets[index];
            
            // 生成唯一名称
            const timestamp = new Date().getTime();
            const strategyName = `${preset.name}-${timestamp}`;
            
            console.log(`尝试恢复策略: ${strategyName}`, {
              name: strategyName,
              description: preset.description,
              code_length: preset.code ? preset.code.length : 0,
              preset_id: preset.id
            });
            
            // 创建一个精简版的策略，只包含必要字段
            const strategyData = {
              name: strategyName,
              description: preset.description || '预设策略',
              code: preset.code,
              preset_id: preset.id
            };
            
            // 使用axios直接发送请求，而不是通过Vuex
            const token = localStorage.getItem('token');
            const response = await axios.post('http://localhost:8000/api/strategies/', strategyData, {
              headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json'
              }
            });
            
            console.log(`成功恢复策略: ${strategyName}`, response.data);
            this.addedCount++;
            
            // 添加短暂延迟，避免服务器压力
            await new Promise(resolve => setTimeout(resolve, 300));
          } catch (err) {
            console.error('恢复策略错误:', err);
            console.error('错误详情:', {
              message: err.message,
              status: err.response?.status,
              data: err.response?.data
            });
            
            // 继续添加其他策略
            continue;
          }
        }
        
        // 刷新策略列表
        await this.fetchStrategies();
        
        // 关闭模态框
        if (this.deletedPresetModal) {
          this.deletedPresetModal.hide();
        }
        this.selectedPresets = [];
        
        // 显示成功消息
        this.$emit('alert', `成功恢复了 ${this.addedCount} 个预设策略`, 'success');
      } catch (error) {
        console.error('恢复预设策略过程中发生错误:', error);
        this.$emit('alert', '恢复预设策略失败: ' + (error.message || '未知错误'), 'danger');
      } finally {
        this.addingPresets = false;
        this.addedCount = 0;
        
        // 重新获取已删除的预设策略
        await this.fetchDeletedPresetStrategies();
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