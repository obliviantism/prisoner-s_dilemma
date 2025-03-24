<template>
  <div class="home">
    <div class="row">
      <div class="col-md-8 offset-md-2 text-center">
        <h1 class="display-4 mb-4">欢迎来到囚徒困境</h1>
        <p class="lead mb-4">
          测试您的策略在这个经典的合作与欺骗博弈中的表现。
          您会选择合作还是欺骗？
        </p>
      </div>
    </div>

    <div class="row mt-4">
      <div class="col-md-4">
        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">您的策略</h5>
            <p class="card-text">创建和管理您的游戏策略。</p>
            <router-link to="/strategies" class="btn btn-primary">查看策略</router-link>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">进行游戏</h5>
            <p class="card-text">开始新游戏或查看进行中的比赛。</p>
            <router-link to="/games" class="btn btn-primary">查看游戏</router-link>
          </div>
        </div>
      </div>
      <div class="col-md-4">
        <div class="card mb-4">
          <div class="card-body">
            <h5 class="card-title">排行榜</h5>
            <p class="card-text">查看您的策略与其他人相比的排名。</p>
            <router-link to="/leaderboard" class="btn btn-primary">查看排行榜</router-link>
          </div>
        </div>
      </div>
    </div>

    <div class="row mt-5" v-if="recentGames.length > 0">
      <div class="col-12">
        <h2>最近的游戏</h2>
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
</template>

<script>
export default {
  name: 'HomePage',
  data() {
    return {
      recentGames: [],
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
  async mounted() {
    if (localStorage.getItem('token')) {
      try {
        const response = await this.$store.dispatch('fetchGames')
        this.recentGames = response.slice(0, 5).map(game => ({
          game_id: game.id,
          strategy1_name: game.strategy1.name,
          strategy2_name: game.strategy2.name,
          status: game.status === 'COMPLETED' ? '已完成' : '进行中',
          player1_score: game.player1_score,
          player2_score: game.player2_score,
          winner: this.determineWinner(game)
        }))
      } catch (error) {
        console.error('Error fetching recent games', error)
      }
    }
  },
  methods: {
    determineWinner(game) {
      if (game.status !== 'COMPLETED') return '进行中'
      if (game.player1_score > game.player2_score) return game.strategy1.name
      if (game.player2_score > game.player1_score) return game.strategy2.name
      return '平局'
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
</style> 