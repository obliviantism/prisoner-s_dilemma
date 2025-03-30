<template>
  <div class="history-page">
    <h1 class="mb-4">游戏历史记录</h1>
    
    <div v-if="loading" class="text-center my-5">
      <loading-spinner text="加载历史记录中..." />
    </div>
    
    <div v-else-if="games.length === 0" class="alert alert-info">
      您还没有任何游戏记录。尝试<router-link to="/games/create">创建一个新游戏</router-link>来开始吧！
    </div>
    
    <div v-else>
      <div class="filters mb-4">
        <div class="row">
          <div class="col-md-8">
            <div class="input-group">
              <input 
                type="text" 
                class="form-control" 
                placeholder="搜索策略名称..." 
                v-model="searchQuery"
              >
              <button 
                class="btn btn-outline-secondary" 
                type="button"
                @click="searchQuery = ''"
                v-if="searchQuery"
              >
                清除
              </button>
            </div>
          </div>
          <div class="col-md-4">
            <select class="form-select" v-model="statusFilter">
              <option value="">所有状态</option>
              <option value="COMPLETED">已完成</option>
              <option value="IN_PROGRESS">进行中</option>
            </select>
          </div>
        </div>
      </div>
      
      <div class="table-responsive">
        <table class="table table-striped table-hover">
          <thead>
            <tr>
              <th>ID</th>
              <th>策略 1</th>
              <th>策略 2</th>
              <th>轮数</th>
              <th>得分</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="game in filteredGames" :key="game.id">
              <td>{{ game.id }}</td>
              <td>{{ game.strategy1.name }}</td>
              <td>{{ game.strategy2.name }}</td>
              <td>{{ game.current_round }} / {{ game.total_rounds }}</td>
              <td>{{ game.player1_score }} - {{ game.player2_score }}</td>
              <td>
                <span 
                  class="badge"
                  :class="{'bg-success': game.status === 'COMPLETED', 'bg-warning': game.status === 'IN_PROGRESS'}"
                >
                  {{ game.status === 'COMPLETED' ? '已完成' : '进行中' }}
                </span>
              </td>
              <td>{{ formatDate(game.created_at) }}</td>
              <td>
                <router-link 
                  :to="`/games/${game.id}`" 
                  class="btn btn-sm btn-outline-primary"
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
import { mapActions } from 'vuex';
import LoadingSpinner from '../components/LoadingSpinner.vue';

export default {
  name: 'HistoryPage',
  components: {
    LoadingSpinner
  },
  data() {
    return {
      loading: true,
      games: [],
      searchQuery: '',
      statusFilter: ''
    }
  },
  computed: {
    filteredGames() {
      return this.games.filter(game => {
        // 状态筛选
        if (this.statusFilter && game.status !== this.statusFilter) {
          return false;
        }
        
        // 搜索查询
        if (this.searchQuery) {
          const query = this.searchQuery.toLowerCase();
          return (
            game.strategy1.name.toLowerCase().includes(query) ||
            game.strategy2.name.toLowerCase().includes(query)
          );
        }
        
        return true;
      });
    }
  },
  methods: {
    ...mapActions(['fetchGames']),
    async loadGames() {
      this.loading = true;
      try {
        this.games = await this.fetchGames();
      } catch (error) {
        console.error('加载游戏历史记录失败:', error);
      } finally {
        this.loading = false;
      }
    },
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleString();
    }
  },
  created() {
    this.loadGames();
  }
}
</script>

<style scoped>
.history-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.filters {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 5px;
}
</style> 