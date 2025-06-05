<template>
  <div class="tournament-results">
    <div v-if="loading" class="text-center my-5">
      <LoadingSpinner />
    </div>
    
    <div v-else-if="error" class="alert alert-danger">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <h4 class="alert-heading"><i class="bi bi-exclamation-triangle-fill me-2"></i>获取锦标赛结果失败</h4>
          <p class="mb-0">{{ error }}</p>
        </div>
        <div>
          <button @click="fetchTournamentResults" class="btn btn-outline-danger me-2">
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
          <h2 class="mb-0">{{ tournament.name }} - 锦标赛结果</h2>
          <router-link :to="`/tournaments/${tournament.id}`" class="btn btn-light">
            <i class="bi bi-arrow-left"></i> 返回详情
          </router-link>
        </div>
        <div class="card-body">
          <div class="row mb-4">
            <div class="col-md-6">
              <h4>锦标赛信息</h4>
              <p>{{ tournament.description }}</p>
              <p>
                <span class="badge bg-success">已完成</span>
                <span class="ms-2">参赛者: {{ tournament.participants ? tournament.participants.length : 0 }}</span>
                <span class="ms-2">每场比赛回合: {{ tournament.rounds_per_match }}</span>
                <span class="ms-2">重复次数: {{ tournament.repetitions }}</span>
              </p>
              <p>
                <strong>创建时间:</strong> {{ formatDate(tournament.created_at) }}<br>
                <strong>完成时间:</strong> {{ formatDate(tournament.completed_at) }}
              </p>
            </div>
            <div class="col-md-6">
              <h4>收益矩阵</h4>
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
          
          <hr>
          
          <h3 class="mb-4">最终排名</h3>
          <div class="table-responsive">
            <table class="table table-striped table-hover">
              <thead class="table-primary">
                <tr>
                  <th>排名</th>
                  <th>策略</th>
                  <th>总分</th>
                  <th>平均分</th>
                  <th>胜场数</th>
                  <th>平局数</th>
                  <th>负场数</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="participant in sortedParticipants" :key="participant.id">
                  <td>
                    <span class="badge" :class="getRankBadgeClass(participant.rank)">{{ participant.rank }}</span>
                  </td>
                  <td>
                    <span>{{ participant.strategy.name }}</span>
                    <small v-if="participant.strategy.description" class="d-block text-muted">
                      {{ truncateText(participant.strategy.description, 80) }}
                    </small>
                  </td>
                  <td>{{ formatScore(participant.total_score) }}</td>
                  <td>{{ formatScore(participant.average_score) }}</td>
                  <td>{{ participant.wins || 0 }}</td>
                  <td>{{ participant.draws || 0 }}</td>
                  <td>{{ participant.losses || 0 }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <h3 class="mb-4 mt-5">对战结果</h3>
          <div class="table-responsive">
            <table class="table table-bordered">
              <thead class="table-secondary">
                <tr>
                  <th></th>
                  <th v-for="participant in sortedParticipants" :key="participant.id">
                    {{ participant.strategy ? participant.strategy.name : '未知策略' }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p1 in sortedParticipants" :key="p1.id">
                  <th class="table-secondary">{{ p1.strategy ? p1.strategy.name : '未知策略' }}</th>
                  <td v-for="p2 in sortedParticipants" :key="p2.id" :class="getCellClass(p1, p2)">
                    <div v-if="p1.id === p2.id" class="text-center">--</div>
                    <div v-else>
                      <div v-if="getMatchDetails(p1, p2) !== 'N/A'">
                        <strong>{{ getMatchResult(p1, p2) }}</strong>
                        <small class="d-block" v-if="getWinLossDraw(p1, p2) !== 'N/A'">
                          {{ getWinLossDraw(p1, p2) }}
                        </small>
                      </div>
                      <div v-else>N/A</div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <div v-if="tournament.match_results && tournament.match_results.length > 0" class="mt-5">
            <h3 class="mb-4">比赛详情</h3>
            
            <div class="accordion" id="matchAccordion">
              <div v-for="(match, index) in tournament.match_results" :key="index" class="accordion-item">
                <h2 class="accordion-header" :id="`heading-${index}`">
                  <button class="accordion-button collapsed" type="button" 
                          data-bs-toggle="collapse" 
                          :data-bs-target="`#collapse-${index}`" 
                          aria-expanded="false" 
                          :aria-controls="`collapse-${index}`">
                    <div class="w-100 d-flex justify-content-between">
                      <span>
                        <strong>{{ getStrategyName(match.strategy1_id) }}</strong> vs 
                        <strong>{{ getStrategyName(match.strategy2_id) }}</strong>
                      </span>
                      <span>
                        得分: {{ formatScore(match.score1) }} - {{ formatScore(match.score2) }}
                      </span>
                    </div>
                  </button>
                </h2>
                <div :id="`collapse-${index}`" class="accordion-collapse collapse" 
                      :aria-labelledby="`heading-${index}`" 
                      data-bs-parent="#matchAccordion">
                  <div class="accordion-body">
                    <div class="row">
                      <div class="col-md-6">
                        <h5>比赛信息</h5>
                        <p>
                          <strong>回合数:</strong> {{ match.rounds ? match.rounds.length : 0 }}<br>
                          <strong>策略1:</strong> {{ getStrategyName(match.strategy1_id) }}<br>
                          <strong>策略2:</strong> {{ getStrategyName(match.strategy2_id) }}<br>
                          <strong>得分:</strong> {{ formatScore(match.score1) }} - {{ formatScore(match.score2) }}
                        </p>
                      </div>
                      <div class="col-md-6">
                        <h5>回合统计</h5>
                        <p>
                          <strong>策略1合作次数:</strong> {{ countMoves(match.rounds, 0, 'C') }}<br>
                          <strong>策略1背叛次数:</strong> {{ countMoves(match.rounds, 0, 'D') }}<br>
                          <strong>策略2合作次数:</strong> {{ countMoves(match.rounds, 1, 'C') }}<br>
                          <strong>策略2背叛次数:</strong> {{ countMoves(match.rounds, 1, 'D') }}
                        </p>
                      </div>
                    </div>
                    
                    <h5 class="mt-3">回合详情</h5>
                    <div class="table-responsive">
                      <table class="table table-sm table-bordered">
                        <thead>
                          <tr>
                            <th>回合</th>
                            <th>{{ getStrategyName(match.strategy1_id) }}</th>
                            <th>{{ getStrategyName(match.strategy2_id) }}</th>
                            <th>策略1得分</th>
                            <th>策略2得分</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(round, roundIndex) in match.rounds || []" :key="roundIndex">
                            <td>{{ roundIndex + 1 }}</td>
                            <td>{{ round && round.moves ? round.moves[0] : 'N/A' }}</td>
                            <td>{{ round && round.moves ? round.moves[1] : 'N/A' }}</td>
                            <td>{{ round && round.scores ? round.scores[0] : 'N/A' }}</td>
                            <td>{{ round && round.scores ? round.scores[1] : 'N/A' }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
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

export default {
  name: 'TournamentResults',
  components: {
    LoadingSpinner
  },
  data() {
    return {
      loading: true,
      error: null,
      matchMatrix: {}
    }
  },
  computed: {
    ...mapGetters(['currentTournament']),
    tournament() {
      return this.currentTournament || {}
    },
    sortedParticipants() {
      if (!this.tournament.participants) return []
      
      // 过滤掉没有strategy属性的参赛者
      const validParticipants = this.tournament.participants.filter(p => p && p.strategy)
      
      // 按排名排序
      return [...validParticipants].sort((a, b) => {
        return a.rank - b.rank
      })
    }
  },
  methods: {
    async fetchTournamentResults() {
      this.loading = true
      this.error = null
      
      try {
        await this.$store.dispatch('getTournamentResults', this.$route.params.id)
        console.log('API返回的锦标赛结果数据:', this.tournament)
        
        // 检查是否有必要的数据
        if (!this.tournament || !this.tournament.id) {
          throw new Error('无法加载锦标赛数据，请确认锦标赛是否存在')
        }
        
        // 检查matchups_matrix数据结构
        console.log('matchups_matrix数据结构:', this.tournament.matchups_matrix)
        if (!this.tournament.matchups_matrix) {
          console.warn('警告：锦标赛没有matchups_matrix数据')
        } else {
          console.log('matchups_matrix类型:', typeof this.tournament.matchups_matrix)
          console.log('matchups_matrix是否为对象:', this.tournament.matchups_matrix instanceof Object)
        }
        
        // 构建对战矩阵
        this.buildMatchMatrix()
      } catch (error) {
        console.error('获取锦标赛结果失败:', error)
        
        // 记录更详细的错误信息
        if (error.response) {
          console.error('错误响应状态:', error.response.status)
          console.error('错误响应数据:', error.response.data)
        }
        
        this.error = error.message || '获取锦标赛结果失败，请重试'
      } finally {
        this.loading = false
      }
    },
    buildMatchMatrix() {
      // 构建对战矩阵，方便查询
      this.matchMatrix = {}
      
      // 使用后端提供的matchups_matrix
      if (!this.tournament.matchups_matrix) {
        console.error('matchups_matrix不存在!', this.tournament)
        // 确保不返回undefined，而是空数组，避免后续操作中的空指针异常
        this.tournament.matchups_matrix = []
        return
      }
      
      console.log('使用matchups_matrix构建对战矩阵:', this.tournament.matchups_matrix)
      
      // 直接使用后端提供的对战矩阵数据
      this.matchMatrix = this.tournament.matchups_matrix
      console.log('构建的matchMatrix:', this.matchMatrix)
    },
    getMatchResult(p1, p2) {
      if (!p1 || !p2) return 'N/A'
      
      // 检查strategy是否存在
      if (!p1.strategy || !p2.strategy) {
        console.error('策略不存在:', p1, p2)
        return 'N/A'
      }
      
      // 使用嵌套对象格式的matchups_matrix
      if (this.tournament.matchups_matrix) {
        const p1Name = p1.strategy.name
        const p2Name = p2.strategy.name
        
        // 检查matchups_matrix是否有对应的数据
        if (this.tournament.matchups_matrix[p1Name] 
            && this.tournament.matchups_matrix[p1Name][p2Name] 
            && this.tournament.matchups_matrix[p1Name][p2Name] !== 'N/A') {
          const matchData = this.tournament.matchups_matrix[p1Name][p2Name]
          return this.formatScore(matchData.avg_score)
        }
      }
      
      return 'N/A'
    },
    getCellClass(p1, p2) {
      if (!p1 || !p2) return ''
      
      // 检查strategy是否存在
      if (!p1.strategy || !p2.strategy) {
        return 'na-cell'
      }
      
      // 如果是自己与自己的对决
      if (p1.id === p2.id) return 'self-match'
      
      // 检查matchups_matrix是否有对应的数据
      const p1Name = p1.strategy.name
      const p2Name = p2.strategy.name
      
      if (this.tournament.matchups_matrix 
          && this.tournament.matchups_matrix[p1Name] 
          && this.tournament.matchups_matrix[p1Name][p2Name]
          && this.tournament.matchups_matrix[p1Name][p2Name] !== 'N/A') {
        
        const matchData = this.tournament.matchups_matrix[p1Name][p2Name]
        
        // 根据胜负情况设置样式
        if (matchData.wins > matchData.losses) return 'win-cell'
        if (matchData.losses > matchData.wins) return 'loss-cell'
        return 'draw-cell'
      }
      
      return 'na-cell'
    },
    getStrategyName(strategyId) {
      if (!this.tournament.participants) return strategyId
      
      const participant = this.tournament.participants.find(p => p && p.strategy && p.strategy.id === strategyId)
      return participant && participant.strategy ? participant.strategy.name : strategyId
    },
    countMoves(rounds, playerIndex, move) {
      if (!rounds) return 0
      return rounds.filter(r => r.moves[playerIndex] === move).length
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
    getRankBadgeClass(rank) {
      if (rank === 1) return 'bg-warning text-dark' // 金牌
      if (rank === 2) return 'bg-secondary' // 银牌
      if (rank === 3) return 'bg-danger' // 铜牌
      return 'bg-primary'
    },
    getMatchDetails(p1, p2) {
      if (!p1 || !p2) return 'N/A'
      
      // 检查strategy是否存在
      if (!p1.strategy || !p2.strategy) {
        console.error('策略不存在:', p1, p2)
        return 'N/A'
      }
      
      // 使用嵌套对象格式的matchups_matrix
      if (this.tournament.matchups_matrix) {
        const p1Name = p1.strategy.name
        const p2Name = p2.strategy.name
        
        // 检查matchups_matrix是否有对应的数据
        if (this.tournament.matchups_matrix[p1Name] 
            && this.tournament.matchups_matrix[p1Name][p2Name] 
            && this.tournament.matchups_matrix[p1Name][p2Name] !== 'N/A') {
          const matchData = this.tournament.matchups_matrix[p1Name][p2Name]
          return this.formatScore(matchData.avg_score)
        }
      }
      
      return 'N/A'
    },
    getWinLossDraw(p1, p2) {
      if (!p1 || !p2) return 'N/A'
      
      // 检查strategy是否存在
      if (!p1.strategy || !p2.strategy) {
        console.error('策略不存在:', p1, p2)
        return 'N/A'
      }
      
      // 使用嵌套对象格式的matchups_matrix
      if (this.tournament.matchups_matrix) {
        const p1Name = p1.strategy.name
        const p2Name = p2.strategy.name
        
        // 检查matchups_matrix是否有对应的数据
        if (this.tournament.matchups_matrix[p1Name] 
            && this.tournament.matchups_matrix[p1Name][p2Name] 
            && this.tournament.matchups_matrix[p1Name][p2Name] !== 'N/A') {
          const matchData = this.tournament.matchups_matrix[p1Name][p2Name]
          return `${matchData.wins}胜/${matchData.draws}平/${matchData.losses}负`
        }
      }
      
      return 'N/A'
    }
  },
  created() {
    this.fetchTournamentResults()
  }
}
</script>

<style scoped>
.tournament-results {
  padding: 20px 0;
}

.table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: #fff;
}

.self-match {
  background-color: #f8f9fa;
  text-align: center;
}

.na-cell {
  background-color: #f5f5f5;
  color: #999;
}

.win-cell {
  background-color: #d1e7dd;  /* 绿色，表示胜利 */
}

.loss-cell {
  background-color: #f8d7da;  /* 红色，表示失败 */
}

.draw-cell {
  background-color: #fff3cd;  /* 黄色，表示平局 */
}
</style> 