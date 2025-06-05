<template>
  <div class="tournament-detail">
    <div v-if="loading" class="text-center my-5">
      <LoadingSpinner />
    </div>
    
    <div v-else-if="error" class="alert alert-danger">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <h4 class="alert-heading"><i class="bi bi-exclamation-triangle-fill me-2"></i>获取锦标赛详情失败</h4>
          <p class="mb-0">{{ error }}</p>
        </div>
        <div>
          <button @click="fetchTournament" class="btn btn-outline-danger me-2">
            <i class="bi bi-arrow-clockwise me-1"></i>重试
          </button>
          <router-link to="/tournaments" class="btn btn-outline-primary">
            <i class="bi bi-arrow-left me-1"></i>返回列表
          </router-link>
        </div>
      </div>
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
            <button v-if="tournament.status === 'COMPLETED' && tournament.id" 
                   @click="checkResultsAvailable" 
                   class="btn btn-info ms-2">
              <i class="bi bi-search"></i> 检查结果数据
            </button>
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
                  <p><strong>每场比赛回合数：</strong> 
                    <span v-if="tournament.use_random_rounds">
                      随机 ({{ tournament.min_rounds }}-{{ tournament.max_rounds }})
                    </span>
                    <span v-else>
                      固定 ({{ tournament.rounds_per_match }})
                    </span>
                  </p>
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
                  <th>胜场数</th>
                  <th>平局数</th>
                  <th>负场数</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="participant in sortedParticipants" :key="participant.id">
                  <td>{{ participant.rank || '-' }}</td>
                  <td>{{ participant.strategy.name }}</td>
                  <td>{{ formatScore(participant.total_score) }}</td>
                  <td>{{ formatScore(participant.average_score) }}</td>
                  <td>{{ participant.wins || '-' }}</td>
                  <td>{{ participant.draws || '-' }}</td>
                  <td>{{ participant.losses || '-' }}</td>
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
      <BaseModal :show="showModal" title="添加参赛者" @close="showModal = false">
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
                      <th style="width: 50px;">
                        <div class="form-check">
                          <input class="form-check-input" type="checkbox" 
                                id="select-all-strategies"
                                v-model="selectAllChecked"
                                @change="toggleSelectAll">
                          <label class="form-check-label" for="select-all-strategies">全选</label>
                        </div>
                      </th>
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
        
        <template #footer>
          <button type="button" class="btn btn-outline-primary me-auto" 
                 @click="selectAllStrategies">
            <i class="bi bi-check-all"></i> 全选策略
          </button>
          <button type="button" class="btn btn-outline-secondary" 
                 @click="clearAllStrategies">
            <i class="bi bi-x-lg"></i> 取消全选
          </button>
          <button type="button" class="btn btn-secondary" @click="showModal = false">取消</button>
          <button type="button" class="btn btn-primary" 
                @click="confirmAddParticipants" 
                :disabled="selectedStrategies.length === 0 || addingParticipants">
            <span v-if="addingParticipants" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
            {{ addingParticipants ? '添加中...' : '添加选中的策略' }}
          </button>
        </template>
      </BaseModal>
    </div>
    
    <!-- 调试区域 (仅限开发环境) -->
    <div v-if="isDevelopment" class="card mt-4 border-warning">
      <div class="card-header bg-warning text-dark">
        <h3 class="mb-0">调试区域</h3>
      </div>
      <div class="card-body">
        <h5>锦标赛信息</h5>
        <p>
          <strong>ID:</strong> {{ tournament.id }}<br>
          <strong>状态:</strong> {{ tournament.status }}<br>
          <strong>数据结构:</strong> {{ Object.keys(tournament).join(', ') }}
        </p>
        
        <div class="mb-3">
          <button @click="debugFetchResults" class="btn btn-outline-primary">
            直接调用 API 获取结果
          </button>
          <button @click="debugTestMatchupsMatrix" class="btn btn-outline-info ms-2">
            测试构建对战矩阵
          </button>
        </div>
        
        <div v-if="debugResult" class="alert" :class="debugSuccess ? 'alert-success' : 'alert-danger'">
          <pre class="mb-0">{{ JSON.stringify(debugResult, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import BaseModal from '@/components/BaseModal.vue'

export default {
  name: 'TournamentDetail',
  components: {
    LoadingSpinner,
    BaseModal
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
      selectAllChecked: false,
      showModal: false,
      debugResult: null,
      debugSuccess: false,
      isDevelopment: process.env.NODE_ENV === 'development'
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
  watch: {
    selectedStrategies(newVal) {
      // 如果所有可用策略都被选中，则自动勾选全选框
      if (this.availableStrategies.length > 0) {
        this.selectAllChecked = newVal.length === this.availableStrategies.length
      }
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
        // 如果有具体错误消息，则显示它，否则使用默认消息
        this.error = error.message || '获取锦标赛详情失败，请重试'
        
        // 如果是404错误（找不到锦标赛），提供更友好的提示并添加返回按钮
        if (error.message && error.message.includes('找不到指定的锦标赛')) {
          this.error = '找不到该锦标赛，可能已被删除或者您没有权限访问。'
          // 错误3秒后自动返回列表页
          setTimeout(() => {
            this.$router.push('/tournaments')
          }, 3000)
        }
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
      this.selectAllChecked = false
      this.fetchAvailableStrategies()
      this.showModal = true
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
        this.showModal = false
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
    toggleSelectAll() {
      if (this.selectAllChecked) {
        // 全选所有可用策略
        this.selectedStrategies = this.availableStrategies.map(strategy => strategy.id)
      } else {
        // 取消全选
        this.selectedStrategies = []
      }
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
    },
    selectAllStrategies() {
      this.selectedStrategies = this.availableStrategies.map(strategy => strategy.id)
      this.selectAllChecked = true
    },
    clearAllStrategies() {
      this.selectedStrategies = []
      this.selectAllChecked = false
    },
    async debugFetchResults() {
      try {
        const response = await this.$store.dispatch('getTournamentResults', this.tournament.id)
        this.debugResult = response
        this.debugSuccess = true
      } catch (error) {
        console.error('调试API调用失败:', error)
        this.debugResult = {
          error: error.message,
          details: error.response ? {
            status: error.response.status,
            data: error.response.data
          } : 'No response details'
        }
        this.debugSuccess = false
      }
    },
    async debugTestMatchupsMatrix() {
      try {
        // 获取锦标赛详情
        const tournamentData = await this.$store.dispatch('fetchTournament', this.tournament.id)
        
        // 分析参赛者数据结构
        const participantsInfo = tournamentData.participants ? tournamentData.participants.map(p => ({
          id: p.id,
          hasStrategy: !!p.strategy,
          strategyId: p.strategy ? p.strategy.id : null,
          strategyName: p.strategy ? p.strategy.name : null
        })) : []
        
        this.debugResult = {
          tournamentFound: !!tournamentData,
          tournamentStatus: tournamentData.status,
          participantsCount: participantsInfo.length,
          participantsInfo,
          hasMatchupsMatrix: !!tournamentData.matchups_matrix,
          matchupsMatrixType: tournamentData.matchups_matrix ? typeof tournamentData.matchups_matrix : 'undefined',
        }
        
        this.debugSuccess = true
      } catch (error) {
        console.error('调试测试失败:', error)
        this.debugResult = {
          error: error.message,
          details: error.response ? {
            status: error.response.status,
            data: error.response.data
          } : 'No response details'
        }
        this.debugSuccess = false
      }
    },
    async checkResultsAvailable() {
      try {
        this.isProcessing = true
        await this.$store.dispatch('getTournamentResults', this.tournament.id)
        this.$router.push(`/tournaments/${this.tournament.id}/results`)
      } catch (error) {
        // 显示更友好的错误提示
        this.$bvToast.toast(`无法获取结果: ${error.message}`, {
          title: '结果检查失败',
          variant: 'danger',
          solid: true
        })
        console.error('检查结果失败:', error)
      } finally {
        this.isProcessing = false
      }
    }
  },
  created() {
    this.fetchTournament()
  },
  beforeRouteLeave(to, from, next) {
    // 确保在导航离开前关闭Modal
    this.showModal = false
    next()
  }
}
</script>

<style scoped>
.tournament-detail {
  padding: 20px 0;
}
</style> 