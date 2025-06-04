<template>
  <div class="tournament-detail">
    <div v-if="loading" class="text-center my-5">
      <LoadingSpinner />
    </div>
    
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>
    
    <div v-else>
      <div class="card mb-4">
        <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
          <h2 class="mb-0">{{ tournament.name }}</h2>
          <div>
            <button v-if="tournament.status === 'CREATED'" 
                   @click="addParticipant" 
                   class="btn btn-light me-2">
              <i class="bi bi-person-plus"></i> 添加参赛者
            </button>
            <button v-if="tournament.status === 'CREATED'" 
                   @click="startTournament" 
                   class="btn btn-warning" 
                   :disabled="isProcessing">
              <i class="bi bi-play-fill"></i> 开始锦标赛
            </button>
            <button v-if="tournament.status === 'IN_PROGRESS'" 
                   @click="runTournament" 
                   class="btn btn-warning" 
                   :disabled="isProcessing">
              <i class="bi bi-lightning"></i> 运行锦标赛
            </button>
            <router-link v-if="tournament.status === 'COMPLETED'" 
                        :to="`/tournaments/${tournament.id}/results`" 
                        class="btn btn-success">
              <i class="bi bi-trophy"></i> 查看结果
            </router-link>
          </div>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-8">
              <h5>锦标赛信息</h5>
              <p>{{ tournament.description }}</p>
              
              <div class="row">
                <div class="col-md-6">
                  <p><strong>状态：</strong> 
                    <span class="badge" :class="getBadgeClass(tournament.status)">
                      {{ getStatusText(tournament.status) }}
                    </span>
                  </p>
                  <p><strong>每场比赛回合数：</strong> {{ tournament.rounds_per_match }}</p>
                  <p><strong>重复次数：</strong> {{ tournament.repetitions }}</p>
                </div>
                <div class="col-md-6">
                  <p><strong>创建者：</strong> {{ tournament.created_by_username }}</p>
                  <p><strong>创建时间：</strong> {{ formatDate(tournament.created_at) }}</p>
                  <p v-if="tournament.completed_at">
                    <strong>完成时间：</strong> {{ formatDate(tournament.completed_at) }}
                  </p>
                </div>
              </div>
            </div>
            <div class="col-md-4">
              <h5>收益矩阵</h5>
              <table class="table table-sm table-bordered">
                <thead class="table-light">
                  <tr>
                    <th></th>
                    <th>玩家2合作(C)</th>
                    <th>玩家2背叛(D)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <th class="table-light">玩家1合作(C)</th>
                    <td>{{ tournament.payoff_matrix?.CC?.[0] }}, {{ tournament.payoff_matrix?.CC?.[1] }}</td>
                    <td>{{ tournament.payoff_matrix?.CD?.[0] }}, {{ tournament.payoff_matrix?.CD?.[1] }}</td>
                  </tr>
                  <tr>
                    <th class="table-light">玩家1背叛(D)</th>
                    <td>{{ tournament.payoff_matrix?.DC?.[0] }}, {{ tournament.payoff_matrix?.DC?.[1] }}</td>
                    <td>{{ tournament.payoff_matrix?.DD?.[0] }}, {{ tournament.payoff_matrix?.DD?.[1] }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-header bg-primary text-white">
          <h3 class="mb-0">参赛者 ({{ tournament.participants ? tournament.participants.length : 0 }})</h3>
        </div>
        <div class="card-body">
          <div v-if="tournament.participants && tournament.participants.length > 0" class="table-responsive">
            <table class="table table-striped">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>策略名称</th>
                  <th>总分</th>
                  <th>平均分</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="participant in sortedParticipants" :key="participant.id">
                  <td>{{ participant.rank || '-' }}</td>
                  <td>{{ participant.strategy.name }}</td>
                  <td>{{ formatScore(participant.total_score) }}</td>
                  <td>{{ formatScore(participant.average_score) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="alert alert-info">
            <p>还没有添加参赛者到此锦标赛。</p>
            <button v-if="tournament.status === 'CREATED'" 
                   @click="addParticipant" 
                   class="btn btn-primary mt-2">
              <i class="bi bi-person-plus"></i> 添加参赛者
            </button>
          </div>
        </div>
      </div>
      
      <!-- 添加参赛者模态框 -->
      <div class="modal fade" id="addParticipantModal" tabindex="-1" aria-labelledby="addParticipantModalLabel" aria-hidden="true" ref="addParticipantModal">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="addParticipantModalLabel">添加参赛者</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <div v-if="loadingStrategies" class="text-center my-3">
                <LoadingSpinner />
              </div>
              <div v-else-if="availableStrategies.length === 0" class="alert alert-info">
                没有可添加的策略。请先创建一些策略。
              </div>
              <div v-else>
                <form>
                  <div class="mb-3">
                    <label class="form-label">选择要添加的策略</label>
                    <div class="table-responsive">
                      <table class="table table-striped">
                        <thead>
                          <tr>
                            <th style="width: 50px;"></th>
                            <th>策略名称</th>
                            <th>描述</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="strategy in availableStrategies" :key="strategy.id">
                            <td>
                              <div class="form-check">
                                <input class="form-check-input" type="checkbox" 
                                      :id="'strategy-' + strategy.id"
                                      v-model="selectedStrategies" 
                                      :value="strategy.id">
                              </div>
                            </td>
                            <td>{{ strategy.name }}</td>
                            <td>{{ truncateText(strategy.description, 100) }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </form>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
              <button type="button" class="btn btn-primary" 
                    @click="confirmAddParticipants" 
                    :disabled="selectedStrategies.length === 0 || addingParticipants">
                <span v-if="addingParticipants" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                {{ addingParticipants ? '添加中...' : '添加选中的策略' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import { Modal } from 'bootstrap'

export default {
  name: 'TournamentDetail',
  components: {
    LoadingSpinner
  },
  data() {
    return {
      loading: true,
      error: null,
      isProcessing: false,
      loadingStrategies: false,
      addingParticipants: false,
      availableStrategies: [],
      selectedStrategies: [],
      modal: null
    }
  },
  computed: {
    ...mapGetters(['currentTournament', 'strategies']),
    tournament() {
      return this.currentTournament || {}
    },
    sortedParticipants() {
      if (!this.tournament.participants) return []
      
      return [...this.tournament.participants].sort((a, b) => {
        // 如果有排名，按排名排序
        if (a.rank && b.rank) return a.rank - b.rank
        // 如果只有一个有排名，有排名的排前面
        if (a.rank) return -1
        if (b.rank) return 1
        // 都没有排名，按平均分排序
        return b.average_score - a.average_score
      })
    }
  },
  methods: {
    async fetchTournament() {
      this.loading = true
      this.error = null
      
      try {
        await this.$store.dispatch('fetchTournament', this.$route.params.id)
      } catch (error) {
        console.error('获取锦标赛详情失败:', error)
        this.error = '获取锦标赛详情失败，请重试'
      } finally {
        this.loading = false
      }
    },
    async fetchAvailableStrategies() {
      this.loadingStrategies = true
      this.availableStrategies = []
      
      try {
        await this.$store.dispatch('fetchStrategies')
        
        // 过滤掉已经添加的策略
        const existingStrategyIds = this.tournament.participants
          ? this.tournament.participants.map(p => p.strategy.id)
          : []
        
        this.availableStrategies = this.strategies.filter(s => !existingStrategyIds.includes(s.id))
      } catch (error) {
        console.error('获取可用策略失败:', error)
        this.$emit('alert', '获取可用策略失败，请重试', 'danger')
      } finally {
        this.loadingStrategies = false
      }
    },
    addParticipant() {
      this.selectedStrategies = []
      this.fetchAvailableStrategies()
      if (this.modal) {
        this.modal.show()
      } else {
        this.$nextTick(() => {
          if (this.$refs.addParticipantModal) {
            if (window.bootstrap) {
              this.modal = new window.bootstrap.Modal(this.$refs.addParticipantModal)
            } else {
              this.modal = new Modal(this.$refs.addParticipantModal)
            }
            this.modal.show()
          } else {
            console.error('Modal element not found')
          }
        })
      }
    },
    async confirmAddParticipants() {
      if (this.selectedStrategies.length === 0) return
      
      this.addingParticipants = true
      
      try {
        // 逐个添加选中的策略
        for (const strategyId of this.selectedStrategies) {
          await this.$store.dispatch('addParticipant', {
            tournamentId: this.tournament.id,
            strategyId
          })
        }
        
        // 刷新锦标赛详情
        await this.fetchTournament()
        
        // 关闭模态框并显示成功消息
        if (this.modal) {
          this.modal.hide()
        }
        this.$emit('alert', `成功添加了 ${this.selectedStrategies.length} 个参赛者`, 'success')
        
        // 清空选择列表
        this.selectedStrategies = []
      } catch (error) {
        console.error('添加参赛者失败:', error)
        this.$emit('alert', '添加参赛者失败，请重试', 'danger')
      } finally {
        this.addingParticipants = false
      }
    },
    async startTournament() {
      if (this.tournament.status !== 'CREATED') return
      if (this.isProcessing) return
      
      this.isProcessing = true
      
      try {
        await this.$store.dispatch('startTournament', this.tournament.id)
        await this.fetchTournament()
        this.$emit('alert', '锦标赛已开始', 'success')
      } catch (error) {
        console.error('开始锦标赛失败:', error)
        this.$emit('alert', '开始锦标赛失败，请重试', 'danger')
      } finally {
        this.isProcessing = false
      }
    },
    async runTournament() {
      if (this.tournament.status !== 'IN_PROGRESS') return
      if (this.isProcessing) return
      
      this.isProcessing = true
      
      try {
        await this.$store.dispatch('runTournament', this.tournament.id)
        await this.fetchTournament()
        this.$emit('alert', '锦标赛已完成', 'success')
      } catch (error) {
        console.error('运行锦标赛失败:', error)
        this.$emit('alert', '运行锦标赛失败，请重试', 'danger')
      } finally {
        this.isProcessing = false
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    formatScore(score) {
      if (score === null || score === undefined) return '-'
      return Number(score).toFixed(2)
    },
    truncateText(text, maxLength) {
      if (!text) return ''
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
    },
    getBadgeClass(status) {
      switch (status) {
        case 'CREATED': return 'bg-info'
        case 'IN_PROGRESS': return 'bg-warning'
        case 'COMPLETED': return 'bg-success'
        default: return 'bg-secondary'
      }
    },
    getStatusText(status) {
      switch (status) {
        case 'CREATED': return '已创建'
        case 'IN_PROGRESS': return '进行中'
        case 'COMPLETED': return '已完成'
        default: return '未知'
      }
    }
  },
  mounted() {
    // 初始化Bootstrap模态框
    this.$nextTick(() => {
      if (this.$refs.addParticipantModal) {
        // 使用全局Bootstrap实例
        if (window.bootstrap) {
          this.modal = new window.bootstrap.Modal(this.$refs.addParticipantModal);
        } else {
          // 如果全局实例不可用，则使用导入的Modal
          this.modal = new Modal(this.$refs.addParticipantModal);
        }
      }
    });
  },
  created() {
    this.fetchTournament()
  },
  beforeUnmount() {
    // 清理Bootstrap模态框
    if (this.modal) {
      this.modal.dispose()
    }
  }
}
</script>

<style scoped>
.tournament-detail {
  padding: 20px 0;
}
</style> 