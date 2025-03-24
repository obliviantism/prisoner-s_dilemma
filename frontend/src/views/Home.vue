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
        <b-card title="您的策略" class="mb-4">
          <b-card-text>创建和管理您的游戏策略。</b-card-text>
          <b-button variant="primary" to="/strategies">查看策略</b-button>
        </b-card>
      </div>
      <div class="col-md-4">
        <b-card title="进行游戏" class="mb-4">
          <b-card-text>开始新游戏或查看进行中的比赛。</b-card-text>
          <b-button variant="primary" to="/games">查看游戏</b-button>
        </b-card>
      </div>
      <div class="col-md-4">
        <b-card title="排行榜" class="mb-4">
          <b-card-text>查看您的策略与其他人相比的排名。</b-card-text>
          <b-button variant="primary" to="/leaderboard">查看排行榜</b-button>
        </b-card>
      </div>
    </div>

    <div class="row mt-5" v-if="recentGames.length > 0">
      <div class="col-12">
        <h2>最近的游戏</h2>
        <b-table
          striped
          hover
          :items="recentGames"
          :fields="fields"
        >
          <template #cell(strategy1)="data">
            {{ data.item.strategy1_name }}
          </template>
          <template #cell(strategy2)="data">
            {{ data.item.strategy2_name }}
          </template>
          <template #cell(score)="data">
            {{ data.item.player1_score }} - {{ data.item.player2_score }}
          </template>
          <template #cell(actions)="data">
            <b-button
              size="sm"
              variant="outline-primary"
              :to="`/games/${data.item.game_id}`"
            >
              查看详情
            </b-button>
          </template>
        </b-table>
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions } from 'vuex'

export default {
  name: 'Home',
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
        const response = await this.fetchGames()
        this.recentGames = response.data.slice(0, 5).map(game => ({
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
    ...mapActions(['fetchGames']),
    
    determineWinner(game) {
      if (game.status !== 'COMPLETED') return '进行中'
      if (game.player1_score > game.player2_score) return game.strategy1.name
      if (game.player2_score > game.player1_score) return game.strategy2.name
      return '平局'
    }
  }
}
</script> 