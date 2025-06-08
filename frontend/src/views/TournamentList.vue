<template>
  <div class="tournament-list">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1>锦标赛</h1>
      <router-link to="/tournaments/create" class="btn btn-primary">
        <i class="bi bi-plus-circle"></i> 创建锦标赛
      </router-link>
    </div>
    
    <div v-if="loading" class="text-center my-5">
      <LoadingSpinner />
    </div>
    
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>
    
    <div v-else-if="tournaments.length === 0" class="alert alert-info">
      <p>暂无锦标赛，点击"创建锦标赛"按钮开始创建。</p>
    </div>
    
    <div v-else class="card">
      <div class="card-header bg-primary text-white">
        <h5 class="mb-0">锦标赛列表</h5>
      </div>
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-striped table-hover mb-0">
            <thead>
              <tr>
                <th>名称</th>
                <th>描述</th>
                <th>状态</th>
                <th>参与者数</th>
                <th>回合数</th>
                <th>重复次数</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tournament in tournaments" :key="tournament.id">
                <td>
                  <router-link :to="`/tournaments/${tournament.id}`">
                    {{ tournament.name }}
                  </router-link>
                </td>
                <td>{{ truncateText(tournament.description, 50) }}</td>
                <td>
                  <span class="badge" :class="getBadgeClass(tournament.status)">
                    {{ getStatusText(tournament.status) }}
                  </span>
                </td>
                <td>{{ tournament.participants ? tournament.participants.length : 0 }}</td>
                <td>
                  <span v-if="tournament.use_probability_model" title="概率模型">
                    {{ (tournament.continue_probability * 100).toFixed(4) }}% 概率
                    <small v-if="tournament.continue_probability === 1" class="d-block">
                      (最多 {{ tournament.rounds_per_match }} 回合)
                    </small>
                  </span>
                  <span v-else-if="tournament.use_random_rounds" title="随机回合数">
                    {{ tournament.min_rounds }}-{{ tournament.max_rounds }} (随机)
                  </span>
                  <span v-else>{{ tournament.rounds_per_match }}</span>
                </td>
                <td>{{ tournament.repetitions }}</td>
                <td>{{ formatDate(tournament.created_at) }}</td>
                <td>
                  <div class="btn-group">
                    <router-link :to="`/tournaments/${tournament.id}`" class="btn btn-sm btn-primary" title="查看详情">
                      <i class="bi bi-eye"></i>
                    </router-link>
                    <router-link v-if="tournament.status === 'COMPLETED'" 
                                :to="`/tournaments/${tournament.id}/results`" 
                                class="btn btn-sm btn-success" 
                                title="查看结果">
                      <i class="bi bi-trophy"></i>
                    </router-link>
                    <button class="btn btn-sm btn-danger" 
                            @click="confirmDelete(tournament)"
                            title="删除锦标赛">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
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
          <p>您确定要删除锦标赛 "{{ tournamentToDelete ? tournamentToDelete.name : '' }}" 吗？</p>
          <p class="text-danger">此操作不可逆，所有关联的比赛记录将被删除。</p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="cancelDelete">取消</button>
          <button type="button" class="btn btn-danger" @click="deleteTournament" :disabled="deleting">
            {{ deleting ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

export default {
  name: 'TournamentList',
  components: {
    LoadingSpinner
  },
  data() {
    return {
      loading: true,
      error: null,
      showDeleteConfirm: false,
      tournamentToDelete: null,
      deleting: false
    }
  },
  computed: {
    ...mapGetters(['tournaments'])
  },
  methods: {
    async fetchTournaments() {
      this.loading = true
      this.error = null
      
      try {
        await this.$store.dispatch('fetchTournaments')
      } catch (error) {
        console.error('获取锦标赛列表失败:', error)
        this.error = '获取锦标赛列表失败，请重试'
      } finally {
        this.loading = false
      }
    },
    truncateText(text, maxLength) {
      if (!text) return ''
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
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
    },
    confirmDelete(tournament) {
      this.tournamentToDelete = tournament
      this.showDeleteConfirm = true
    },
    cancelDelete() {
      this.tournamentToDelete = null
      this.showDeleteConfirm = false
    },
    async deleteTournament() {
      this.deleting = true
      try {
        await this.$store.dispatch('deleteTournament', this.tournamentToDelete.id)
        this.$emit('alert', `锦标赛 "${this.tournamentToDelete.name}" 已成功删除`, 'success')
        this.tournamentToDelete = null
        this.showDeleteConfirm = false
      } catch (error) {
        console.error('删除锦标赛失败:', error)
        this.$emit('alert', `删除锦标赛失败: ${error.response?.data?.error || '请稍后重试'}`, 'danger')
        this.showDeleteConfirm = false
      } finally {
        this.deleting = false
      }
    }
  },
  created() {
    this.fetchTournaments()
  }
}
</script>

<style scoped>
/* 组件样式 */
.tournament-list {
  padding: 20px 0;
}
</style> 