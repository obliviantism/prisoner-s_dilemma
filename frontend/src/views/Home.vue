<template>
  <div class="home">
    <div class="row">
      <div class="col-md-8 offset-md-2 text-center">
        <h1 class="display-4 mb-4">囚徒困境</h1>
        <p class="lead mb-4">
          测试您的策略在这个经典的合作与欺骗博弈中的表现。
        </p>
        <p class="lead mb-4">          
          您会选择合作还是欺骗？
        </p>
      </div>
    </div>

    <div class="row mt-4">
      <div class="col-md-3">
        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">您的策略</h5>
            <p class="card-text">创建和管理您的游戏策略。</p>
            <router-link to="/strategies" class="btn btn-primary">查看策略</router-link>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">进行游戏</h5>
            <p class="card-text">开始新游戏或查看进行中的比赛。</p>
            <router-link to="/games" class="btn btn-primary">查看游戏</router-link>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">锦标赛</h5>
            <p class="card-text">创建或参与多策略对抗的锦标赛。</p>
            <router-link to="/tournaments" class="btn btn-primary">查看锦标赛</router-link>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">排行榜</h5>
            <p class="card-text">查看您的策略与其他人相比的排名。</p>
            <router-link to="/leaderboard" class="btn btn-primary">查看排行榜</router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载中状态 -->
    <div v-if="isLoading" class="my-5">
      <loading-spinner text="数据加载中..." />
    </div>

    <!-- 排行榜信息 -->
    <div class="row mt-5" v-else-if="topStrategies.length > 0">
      <div class="col-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h2 class="mb-0">策略排行榜</h2>
            <router-link to="/leaderboard" class="btn btn-sm btn-outline-primary">查看完整排行榜</router-link>
          </div>
          <div class="card-body">
            <table class="table table-striped table-hover">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>策略名称</th>
                  <th>创建者</th>
                  <th>游戏数</th>
                  <th>平均得分</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(strategy, index) in topStrategies" :key="strategy.strategy_id">
                  <td><strong>{{ index + 1 }}</strong></td>
                  <td>{{ strategy.strategy_name }}</td>
                  <td>{{ strategy.created_by }}</td>
                  <td>{{ strategy.total_games }}</td>
                  <td>{{ strategy.avg_score.toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近的锦标赛 -->
    <div class="row mt-5" v-if="recentTournaments.length > 0">
      <div class="col-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h2 class="mb-0">最近的锦标赛</h2>
            <router-link to="/tournaments" class="btn btn-sm btn-outline-primary">查看全部锦标赛</router-link>
          </div>
          <div class="card-body">
            <table class="table table-striped table-hover">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>参与者数</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="tournament in recentTournaments" :key="tournament.id">
                  <td>{{ tournament.name }}</td>
                  <td>{{ tournament.participants ? tournament.participants.length : 0 }}</td>
                  <td>
                    <span class="badge" :class="getBadgeClass(tournament.status)">
                      {{ getStatusText(tournament.status) }}
                    </span>
                  </td>
                  <td>{{ formatDate(tournament.created_at) }}</td>
                  <td>
                    <div class="btn-group">
                      <router-link 
                        class="btn btn-sm btn-outline-primary"
                        :to="`/tournaments/${tournament.id}`"
                      >
                        查看详情
                      </router-link>
                      <router-link 
                        v-if="tournament.status === 'COMPLETED'" 
                        class="btn btn-sm btn-outline-success"
                        :to="`/tournaments/${tournament.id}/results`"
                      >
                        查看结果
                      </router-link>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <div class="row mt-5" v-if="recentGames.length > 0">
      <div class="col-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h2 class="mb-0">最近的游戏</h2>
            <router-link to="/games" class="btn btn-sm btn-outline-primary">查看全部游戏</router-link>
          </div>
          <div class="card-body">
            <table class="table table-striped table-hover">
              <thead>
                <tr>
                  <th>策略1</th>
                  <th>策略2</th>
                  <th>状态</th>
                  <th>得分</th>
                  <th>获胜者</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="game in recentGames" :key="game.game_id">
                  <td>{{ game.strategy1_name }}</td>
                  <td>{{ game.strategy2_name }}</td>
                  <td>{{ game.status }}</td>
                  <td>{{ game.player1_score }} - {{ game.player2_score }}</td>
                  <td>{{ game.winner }}</td>
                  <td>
                    <router-link 
                      class="btn btn-sm btn-outline-primary"
                      :to="`/games/${game.game_id}`"
                    >
                      查看详情
                    </router-link>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex';
import LoadingSpinner from '../components/LoadingSpinner.vue';

export default {
  name: 'HomePage',
  components: {
    LoadingSpinner
  },
  data() {
    return {
      recentGames: [],
      topStrategies: [],
      recentTournaments: [],
      isLoading: false,
      fields: [
        { key: 'strategy1', label: '策略1' },
        { key: 'strategy2', label: '策略2' },
        { key: 'status', label: '状态' },
        { key: 'score', label: '得分' },
        { key: 'winner', label: '获胜者' },
        { key: 'actions', label: '操作' }
      ]
    }
  },
  computed: {
    ...mapGetters(['isAuthenticated'])
  },
  methods: {
    ...mapActions(['fetchGames', 'fetchLeaderboard', 'fetchTournaments']),
    determineWinner(game) {
      if (game.status !== 'COMPLETED') return '进行中'
      if (game.player1_score > game.player2_score) return game.strategy1.name
      if (game.player2_score > game.player1_score) return game.strategy2.name
      return '平局'
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
  async mounted() {
    if (localStorage.getItem('token')) {
      this.isLoading = true;
      try {
        // 获取最近游戏
        const gamesResponse = await this.fetchGames();
        this.recentGames = gamesResponse.slice(0, 5).map(game => ({
          game_id: game.id,
          strategy1_name: game.strategy1.name,
          strategy2_name: game.strategy2.name,
          status: game.status === 'COMPLETED' ? '已完成' : '进行中',
          player1_score: game.player1_score,
          player2_score: game.player2_score,
          winner: this.determineWinner(game)
        }));

        // 获取排行榜数据
        const leaderboardResponse = await this.fetchLeaderboard();
        this.topStrategies = leaderboardResponse.slice(0, 5); // 只显示前5名
        
        // 获取最近的锦标赛
        const tournamentsResponse = await this.fetchTournaments();
        this.recentTournaments = tournamentsResponse.slice(0, 5); // 只显示前5个锦标赛
      } catch (error) {
        console.error('Error fetching data', error);
      } finally {
        this.isLoading = false;
      }
    }
  }
}
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.btn-group .btn {
  margin-right: 0.25rem;
}

.btn-group .btn:last-child {
  margin-right: 0;
}
</style> 