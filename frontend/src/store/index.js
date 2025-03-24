import { createStore } from 'vuex'
import axios from 'axios'

// 设置axios默认选项
axios.defaults.baseURL = 'http://localhost:8000/api/'
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

// 添加请求拦截器
axios.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Token ${token}`
        }
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

export default createStore({
    state: {
        user: null,
        strategies: [],
        games: [],
        currentGame: null,
        leaderboard: []
    },
    getters: {
        isAuthenticated: state => !!state.user,
        currentUser: state => state.user,
        strategies: state => state.strategies,
        games: state => state.games,
        currentGame: state => state.currentGame,
        leaderboard: state => state.leaderboard
    },
    mutations: {
        setUser(state, user) {
            state.user = user
        },
        setStrategies(state, strategies) {
            state.strategies = strategies
        },
        addStrategy(state, strategy) {
            state.strategies.push(strategy)
        },
        updateStrategy(state, updatedStrategy) {
            const index = state.strategies.findIndex(s => s.id === updatedStrategy.id)
            if (index !== -1) {
                state.strategies.splice(index, 1, updatedStrategy)
            }
        },
        setGames(state, games) {
            state.games = games
        },
        setCurrentGame(state, game) {
            state.currentGame = game
        },
        updateCurrentGame(state, gameData) {
            state.currentGame = { ...state.currentGame, ...gameData }
        },
        setLeaderboard(state, leaderboard) {
            state.leaderboard = leaderboard
        },
        setError(state, errorMessage) {
            // 实际项目中应该添加错误状态管理
            console.error(errorMessage)
        }
    },
    actions: {
        // 身份验证
        async login({ commit }, credentials) {
            const response = await axios.post('auth/login/', credentials)
            const token = response.data.token
            localStorage.setItem('token', token)
            commit('setUser', response.data.user)
            return response
        },
        logout({ commit }) {
            localStorage.removeItem('token')
            commit('setUser', null)
        },

        // 策略
        async fetchStrategies({ commit }) {
            const response = await axios.get('strategies/')
            commit('setStrategies', response.data)
            return response.data
        },
        async createStrategy({ commit }, strategyData) {
            const response = await axios.post('strategies/', strategyData)
            commit('addStrategy', response.data)
            return response.data
        },
        async updateStrategy({ commit }, { id, ...strategyData }) {
            const response = await axios.put(`strategies/${id}/`, strategyData)
            commit('updateStrategy', response.data)
            return response.data
        },

        // 游戏
        async fetchGames({ commit }) {
            const response = await axios.get('games/')
            commit('setGames', response.data)
            return response.data
        },
        async fetchGame({ commit }, id) {
            const response = await axios.get(`games/${id}/`)
            commit('setCurrentGame', response.data)
            return response.data
        },
        async createGame(_, gameData) {
            const response = await axios.post('games/start_game/', gameData)
            return response.data
        },
        async playRound({ commit }, gameId) {
            const response = await axios.post(`games/${gameId}/play_round/`)
            commit('updateCurrentGame', response.data)
            return response.data
        },
        async playFullGame({ commit }, gameId) {
            const response = await axios.post(`games/${gameId}/play_full_game/`)
            commit('updateCurrentGame', response.data)
            return response.data
        },

        // 排行榜
        async fetchLeaderboard({ commit }) {
            const response = await axios.get('leaderboard/')
            commit('setLeaderboard', response.data)
            return response.data
        }
    }
}) 