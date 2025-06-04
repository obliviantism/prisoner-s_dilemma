<template>
  <div class="tournament-results">
    <div v-if="loading" class="text-center my-5">
      <LoadingSpinner />
    </div>
    
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
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
                    {{ participant.strategy.name }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p1 in sortedParticipants" :key="p1.id">
                  <th class="table-secondary">{{ p1.strategy.name }}</th>
                  <td v-for="p2 in sortedParticipants" :key="p2.id" :class="getCellClass(p1, p2)">
                    <div v-if="p1.id === p2.id" class="text-center">--</div>
                    <div v-else>
                      {{ getMatchResult(p1, p2) }}
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
                          <strong>回合数:</strong> {{ match.rounds.length }}<br>
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
                          <tr v-for="(round, roundIndex) in match.rounds" :key="roundIndex">
                            <td>{{ roundIndex + 1 }}</td>
                            <td>{{ round.moves[0] }}</td>
                            <td>{{ round.moves[1] }}</td>
                            <td>{{ round.scores[0] }}</td>
                            <td>{{ round.scores[1] }}</td>
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
      
      return [...this.tournament.participants].sort((a, b) => {
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
        this.buildMatchMatrix()
      } catch (error) {
        console.error('获取锦标赛结果失败:', error)
        this.error = '获取锦标赛结果失败，请重试'
      } finally {
        this.loading = false
      }
    },
    buildMatchMatrix() {
      // 构建对战矩阵，方便查询
      this.matchMatrix = {}
      
      if (!this.tournament.match_results) return
      
      this.tournament.match_results.forEach(match => {
        const key1 = `${match.strategy1_id}-${match.strategy2_id}`
        this.matchMatrix[key1] = {
          score1: match.score1,
          score2: match.score2,
          winner: match.score1 > match.score2 ? 1 : (match.score1 < match.score2 ? 2 : 0)
        }
        
        const key2 = `${match.strategy2_id}-${match.strategy1_id}`
        this.matchMatrix[key2] = {
          score1: match.score2,
          score2: match.score1,
          winner: match.score2 > match.score1 ? 1 : (match.score2 < match.score1 ? 2 : 0)
        }
      })
    },
    getMatchResult(p1, p2) {
      if (p1.id === p2.id) return '--'
      
      const key = `${p1.strategy.id}-${p2.strategy.id}`
      const match = this.matchMatrix[key]
      
      if (!match) return 'N/A'
      
      return `${this.formatScore(match.score1)} - ${this.formatScore(match.score2)}`
    },
    getCellClass(p1, p2) {
      if (p1.id === p2.id) return 'bg-light'
      
      const key = `${p1.strategy.id}-${p2.strategy.id}`
      const match = this.matchMatrix[key]
      
      if (!match) return ''
      
      if (match.winner === 1) return 'bg-success bg-opacity-25'
      if (match.winner === 2) return 'bg-danger bg-opacity-25'
      return 'bg-warning bg-opacity-25' // 平局
    },
    getStrategyName(strategyId) {
      if (!this.tournament.participants) return strategyId
      
      const participant = this.tournament.participants.find(p => p.strategy.id === strategyId)
      return participant ? participant.strategy.name : strategyId
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
</style> 