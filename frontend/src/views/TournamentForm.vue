<template>
  <div class="tournament-form">
    <div class="card">
      <div class="card-header bg-primary text-white">
        <h2 class="mb-0">创建新锦标赛</h2>
      </div>
      <div class="card-body">
        <form @submit.prevent="submitForm">
          <!-- 锦标赛名称 -->
          <div class="mb-3">
            <label for="name" class="form-label">锦标赛名称</label>
            <input 
              type="text" 
              class="form-control" 
              id="name" 
              v-model="formData.name"
              required
              :class="{ 'is-invalid': errors.name }"
            >
            <div class="invalid-feedback" v-if="errors.name">{{ errors.name }}</div>
          </div>
          
          <!-- 锦标赛描述 -->
          <div class="mb-3">
            <label for="description" class="form-label">描述</label>
            <textarea 
              class="form-control" 
              id="description" 
              v-model="formData.description" 
              rows="3"
              :class="{ 'is-invalid': errors.description }"
            ></textarea>
            <div class="invalid-feedback" v-if="errors.description">{{ errors.description }}</div>
          </div>
          
          <!-- 每场比赛回合数和重复次数 -->
          <div class="row">
            <div class="col-md-6 mb-3">
              <label for="rounds_per_match" class="form-label">每场比赛回合数</label>
              <input 
                type="number" 
                class="form-control" 
                id="rounds_per_match" 
                v-model.number="formData.rounds_per_match" 
                min="1"
                :class="{ 'is-invalid': errors.rounds_per_match }"
              >
              <small class="text-muted">每场对局的回合数</small>
              <div class="invalid-feedback" v-if="errors.rounds_per_match">{{ errors.rounds_per_match }}</div>
            </div>
            
            <div class="col-md-6 mb-3">
              <label for="repetitions" class="form-label">重复次数</label>
              <input 
                type="number" 
                class="form-control" 
                id="repetitions" 
                v-model.number="formData.repetitions" 
                min="1"
                :class="{ 'is-invalid': errors.repetitions }"
              >
              <small class="text-muted">每种对阵组合重复的次数</small>
              <div class="invalid-feedback" v-if="errors.repetitions">{{ errors.repetitions }}</div>
            </div>
          </div>
          
          <!-- 自定义收益矩阵 -->
          <div class="card mb-4">
            <div class="card-header">
              <h5>自定义收益矩阵 <span class="text-muted">(可选)</span></h5>
            </div>
            <div class="card-body">
              <p class="text-muted">设置不同选择组合下的收益值。格式为 [玩家1得分, 玩家2得分]</p>
              
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">双方合作 (C,C)</label>
                  <div class="input-group">
                    <input 
                      type="number" 
                      class="form-control" 
                      v-model.number="payoffMatrix.CC[0]" 
                      step="0.1"
                    >
                    <input 
                      type="number" 
                      class="form-control" 
                      v-model.number="payoffMatrix.CC[1]" 
                      step="0.1"
                    >
                  </div>
                </div>
                
                <div class="col-md-6 mb-3">
                  <label class="form-label">玩家1合作，玩家2背叛 (C,D)</label>
                  <div class="input-group">
                    <input 
                      type="number" 
                      class="form-control" 
                      v-model.number="payoffMatrix.CD[0]" 
                      step="0.1"
                    >
                    <input 
                      type="number" 
                      class="form-control" 
                      v-model.number="payoffMatrix.CD[1]" 
                      step="0.1"
                    >
                  </div>
                </div>
                
                <div class="col-md-6 mb-3">
                  <label class="form-label">玩家1背叛，玩家2合作 (D,C)</label>
                  <div class="input-group">
                    <input 
                      type="number" 
                      class="form-control" 
                      v-model.number="payoffMatrix.DC[0]" 
                      step="0.1"
                    >
                    <input 
                      type="number" 
                      class="form-control" 
                      v-model.number="payoffMatrix.DC[1]" 
                      step="0.1"
                    >
                  </div>
                </div>
                
                <div class="col-md-6 mb-3">
                  <label class="form-label">双方背叛 (D,D)</label>
                  <div class="input-group">
                    <input 
                      type="number" 
                      class="form-control" 
                      v-model.number="payoffMatrix.DD[0]" 
                      step="0.1"
                    >
                    <input 
                      type="number" 
                      class="form-control" 
                      v-model.number="payoffMatrix.DD[1]" 
                      step="0.1"
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 表单按钮 -->
          <div class="d-grid gap-2 d-md-flex justify-content-md-end">
            <router-link to="/tournaments" class="btn btn-secondary me-md-2">取消</router-link>
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              <span v-if="submitting" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
              {{ submitting ? '创建中...' : '创建锦标赛' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TournamentForm',
  data() {
    return {
      formData: {
        name: '',
        description: '',
        rounds_per_match: 200,
        repetitions: 5,
      },
      payoffMatrix: {
        CC: [3, 3],
        CD: [0, 5],
        DC: [5, 0],
        DD: [1, 1]
      },
      errors: {},
      submitting: false
    }
  },
  methods: {
    validateForm() {
      this.errors = {}
      
      if (!this.formData.name) {
        this.errors.name = '请输入锦标赛名称'
      }
      
      if (this.formData.rounds_per_match < 1) {
        this.errors.rounds_per_match = '每场比赛回合数必须大于0'
      }
      
      if (this.formData.repetitions < 1) {
        this.errors.repetitions = '重复次数必须大于0'
      }
      
      return Object.keys(this.errors).length === 0
    },
    async submitForm() {
      if (!this.validateForm()) return
      
      this.submitting = true
      
      try {
        // 准备提交数据
        const tournamentData = {
          ...this.formData,
          payoff_matrix: this.payoffMatrix
        }
        
        // 发送请求创建锦标赛
        const response = await this.$store.dispatch('createTournament', tournamentData)
        
        // 显示成功消息并跳转
        this.$emit('alert', '锦标赛创建成功！', 'success')
        this.$router.push(`/tournaments/${response.id}`)
      } catch (error) {
        console.error('创建锦标赛失败:', error)
        
        // 显示错误消息
        if (error.response && error.response.data) {
          // 处理后端返回的错误信息
          const backendErrors = error.response.data
          
          // 如果是详细的字段错误
          if (typeof backendErrors === 'object' && !Array.isArray(backendErrors)) {
            Object.keys(backendErrors).forEach(key => {
              this.errors[key] = Array.isArray(backendErrors[key]) 
                ? backendErrors[key].join(' ') 
                : backendErrors[key]
            })
          } else {
            // 一般错误消息
            this.$emit('alert', typeof backendErrors === 'string' 
              ? backendErrors 
              : '创建锦标赛失败，请重试', 'danger')
          }
        } else {
          this.$emit('alert', '创建锦标赛失败，请重试', 'danger')
        }
      } finally {
        this.submitting = false
      }
    }
  }
}
</script>

<style scoped>
.tournament-form {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 0;
}
</style> 