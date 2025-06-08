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
              <label for="rounds_type" class="form-label">回合数设置</label>
              <div class="form-group mb-3">
                <div class="form-check mb-2">
                  <input 
                    class="form-check-input" 
                    type="radio" 
                    id="fixed_rounds" 
                    value="fixed"
                    v-model="roundsType"
                  >
                  <label class="form-check-label" for="fixed_rounds">
                    使用固定回合数
                  </label>
                </div>
                
                <div class="form-check mb-2">
                  <input 
                    class="form-check-input" 
                    type="radio" 
                    id="random_rounds" 
                    value="random"
                    v-model="roundsType"
                  >
                  <label class="form-check-label" for="random_rounds">
                    使用随机回合数
                  </label>
                </div>
                
                <div class="form-check mb-2">
                  <input 
                    class="form-check-input" 
                    type="radio" 
                    id="probability_model" 
                    value="probability"
                    v-model="roundsType"
                  >
                  <label class="form-check-label" for="probability_model">
                    以w的概率进行下一轮
                  </label>
                </div>
              </div>
              
              <div v-if="roundsType === 'fixed'">
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
              
              <div v-else-if="roundsType === 'random'" class="mt-2">
                <div class="row">
                  <div class="col-md-6">
                    <label for="min_rounds" class="form-label">最小回合数</label>
                    <input 
                      type="number" 
                      class="form-control" 
                      id="min_rounds" 
                      v-model.number="formData.min_rounds" 
                      min="1"
                      :class="{ 'is-invalid': errors.min_rounds }"
                    >
                    <div class="invalid-feedback" v-if="errors.min_rounds">{{ errors.min_rounds }}</div>
                  </div>
                  <div class="col-md-6">
                    <label for="max_rounds" class="form-label">最大回合数</label>
                    <input 
                      type="number" 
                      class="form-control" 
                      id="max_rounds" 
                      v-model.number="formData.max_rounds" 
                      :min="formData.min_rounds + 1"
                      :class="{ 'is-invalid': errors.max_rounds }"
                    >
                    <div class="invalid-feedback" v-if="errors.max_rounds">{{ errors.max_rounds }}</div>
                  </div>
                </div>
                <small class="text-muted d-block mt-1">系统将在指定范围内随机选择每场比赛的回合数</small>
              </div>
              
              <div v-else-if="roundsType === 'probability'" class="mt-2">
                <label for="continue_probability" class="form-label">继续概率 (w):</label>
                <div class="row mb-2">
                  <div class="col-md-8">
                    <input 
                      type="range" 
                      class="form-range" 
                      id="continue_probability" 
                      v-model.number="formData.continue_probability" 
                      min="0" 
                      max="1" 
                      step="0.0001"
                      :class="{ 'is-invalid': errors.continue_probability }"
                    >
                  </div>
                  <div class="col-md-4">
                    <input 
                      type="number" 
                      class="form-control" 
                      v-model.number="formData.continue_probability" 
                      min="0" 
                      max="1" 
                      step="0.0001"
                      :class="{ 'is-invalid': errors.continue_probability }"
                    >
                  </div>
                </div>
                <div class="invalid-feedback" v-if="errors.continue_probability">{{ errors.continue_probability }}</div>
                <small class="text-muted d-block mt-1">每轮对局后，以 {{ (formData.continue_probability * 100).toFixed(4) }}% 的概率继续下一轮</small>
                <small class="text-muted d-block mt-1">
                  平均回合数约为: 
                  <span v-if="formData.continue_probability < 1">
                    {{ Math.round(1 / (1 - formData.continue_probability)) }} 轮
                  </span>
                  <span v-else>
                    最多 {{ formData.rounds_per_match }} 轮
                  </span>
                </small>
                <small v-if="formData.continue_probability === 1" class="text-warning d-block mt-1">
                  <i class="bi bi-exclamation-triangle"></i> 
                  当w=1时，为避免无限循环，系统会限制最多进行 {{ formData.rounds_per_match }} 回合
                </small>
              </div>
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
        use_random_rounds: false,
        use_probability_model: false,
        min_rounds: 100,
        max_rounds: 300,
        continue_probability: 0.95,
        repetitions: 5,
      },
      payoffMatrix: {
        CC: [3, 3],
        CD: [0, 5],
        DC: [5, 0],
        DD: [1, 1]
      },
      errors: {},
      submitting: false,
      roundsType: 'fixed'  // 'fixed', 'random', 或 'probability'
    }
  },
  created() {
    // 根据初始数据设置正确的回合类型
    if (this.formData.use_probability_model) {
      this.roundsType = 'probability';
    } else if (this.formData.use_random_rounds) {
      this.roundsType = 'random';
    } else {
      this.roundsType = 'fixed';
    }
  },
  watch: {
    roundsType(newType) {
      // 根据选择更新相关标志
      if (newType === 'fixed') {
        this.formData.use_random_rounds = false;
        this.formData.use_probability_model = false;
      } else if (newType === 'random') {
        this.formData.use_random_rounds = true;
        this.formData.use_probability_model = false;
      } else if (newType === 'probability') {
        this.formData.use_random_rounds = false;
        this.formData.use_probability_model = true;
      }
    }
  },
  methods: {
    validateForm() {
      this.errors = {}
      
      if (!this.formData.name) {
        this.errors.name = '请输入锦标赛名称'
      }
      
      if (this.roundsType === 'fixed') {
        // 验证固定回合数
        if (this.formData.rounds_per_match < 1) {
          this.errors.rounds_per_match = '每场比赛回合数必须大于0'
        }
      } else if (this.roundsType === 'random') {
        // 验证随机回合数范围
        if (this.formData.min_rounds < 1) {
          this.errors.min_rounds = '最小回合数必须大于0'
        }
        
        if (this.formData.max_rounds <= this.formData.min_rounds) {
          this.errors.max_rounds = '最大回合数必须大于最小回合数'
        }
      } else if (this.roundsType === 'probability') {
        // 验证概率值
        if (this.formData.continue_probability < 0 || this.formData.continue_probability > 1) {
          this.errors.continue_probability = '概率必须在 0-1 之间（包含两端）'
        }
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