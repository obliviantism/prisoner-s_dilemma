import { createStore } from 'vuex'
import axios from 'axios'

// 设置axios默认选项
axios.defaults.baseURL = 'http://localhost:8000/api/'
axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

// API错误处理辅助函数
const handleApiError = (commit, error) => {
    console.error('API 请求错误:', error)
    if (error.response && error.response.data) {
        const errorMessage = error.response.data.error || error.response.data.detail || '请求失败'
        commit('setError', errorMessage)
    } else {
        commit('setError', error.message || '网络错误，请检查您的连接')
    }
}

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
        leaderboard: [],
        tournaments: [],
        currentTournament: null,
        tournamentParticipants: []
    },
    getters: {
        isAuthenticated: state => !!state.user,
        currentUser: state => state.user,
        strategies: state => state.strategies,
        games: state => state.games,
        currentGame: state => state.currentGame,
        leaderboard: state => state.leaderboard,
        tournaments: state => state.tournaments,
        currentTournament: state => state.currentTournament,
        tournamentParticipants: state => state.tournamentParticipants
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
        removeStrategy(state, strategyId) {
            state.strategies = state.strategies.filter(strategy => strategy.id !== strategyId)
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
        setTournaments(state, tournaments) {
            state.tournaments = tournaments
        },
        setCurrentTournament(state, tournament) {
            state.currentTournament = tournament
        },
        updateCurrentTournament(state, tournamentData) {
            state.currentTournament = { ...state.currentTournament, ...tournamentData }
        },
        setTournamentParticipants(state, participants) {
            state.tournamentParticipants = participants
        },
        setError(state, errorMessage) {
            // 实际项目中应该添加错误状态管理
            console.error(errorMessage)
        }
    },
    actions: {
        // 身份验证
        async login({ commit, dispatch }, credentials) {
            const response = await axios.post('auth/login/', credentials)
            const token = response.data.token
            localStorage.setItem('token', token)

            // 如果响应中直接包含用户信息，则使用该信息
            if (response.data.user) {
                commit('setUser', response.data.user)
            } else {
                // 否则获取当前用户信息
                await dispatch('getCurrentUser')
            }

            return response
        },
        async getCurrentUser({ commit }) {
            try {
                const response = await axios.get('auth/user/')
                commit('setUser', response.data)
                return response.data
            } catch (error) {
                console.error('获取用户信息失败:', error)
                // 如果获取用户信息失败，清除token并登出
                localStorage.removeItem('token')
                commit('setUser', null)
                throw error
            }
        },
        // eslint-disable-next-line no-unused-vars
        async restoreSession({ commit, dispatch }) {
            const token = localStorage.getItem('token')
            if (token) {
                try {
                    await dispatch('getCurrentUser')
                    return true
                } catch (error) {
                    return false
                }
            }
            return false
        },
        // eslint-disable-next-line no-unused-vars
        async register({ commit }, userData) {
            const response = await axios.post('auth/register/', userData)
            return response.data
        },
        async logout({ commit }) {
            try {
                const token = localStorage.getItem('token')
                if (token) {
                    // 向服务器发送退出请求
                    await axios.post('auth/logout/')
                }
            } catch (error) {
                console.error('退出时发生错误:', error)
            } finally {
                // 即使服务器请求失败，也要清除本地状态
                localStorage.removeItem('token')
                commit('setUser', null)
            }
        },

        // 策略
        async fetchStrategies({ commit }) {
            const response = await axios.get('strategies/')
            commit('setStrategies', response.data)
            return response.data
        },
        async fetchStrategy(_, id) {
            const response = await axios.get(`strategies/${id}/`)
            return response.data
        },
        async createStrategy({ commit }, strategyData) {
            try {
                console.log(`正在创建策略: ${strategyData.name}`, strategyData)
                const response = await axios.post('strategies/', strategyData)
                console.log(`策略创建成功:`, response.data)
                commit('addStrategy', response.data)
                return response.data
            } catch (error) {
                console.error(`创建策略 "${strategyData.name}" 失败:`, error)

                // 详细记录错误信息
                if (error.response) {
                    console.error('服务器响应:', {
                        status: error.response.status,
                        statusText: error.response.statusText,
                        data: error.response.data
                    })

                    // 如果有详细错误信息，将其作为错误消息
                    if (error.response.data && (error.response.data.error || error.response.data.detail)) {
                        const errorMessage = error.response.data.error || error.response.data.detail
                        handleApiError(commit, { message: errorMessage, response: error.response })
                        throw new Error(errorMessage)
                    }
                }

                // 处理其他类型的错误
                handleApiError(commit, error)
                throw error
            }
        },
        async updateStrategy({ commit }, { id, ...strategyData }) {
            const response = await axios.put(`strategies/${id}/`, strategyData)
            commit('updateStrategy', response.data)
            return response.data
        },
        async deleteStrategy({ commit }, id) {
            try {
                console.log(`开始删除策略，ID: ${id}`)
                const response = await axios.delete(`strategies/${id}/`)
                console.log(`删除策略成功，响应:`, response.data)
                commit('removeStrategy', id)
                return true
            } catch (error) {
                console.error('删除策略失败:', error)
                console.error('错误详情:', {
                    message: error.message,
                    status: error.response?.status,
                    statusText: error.response?.statusText,
                    responseData: error.response?.data
                })
                handleApiError(commit, error)
                throw error
            }
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
        async deleteGame({ dispatch }, gameId) {
            await axios.delete(`games/${gameId}/delete_game/`)
            // 删除游戏后刷新游戏列表
            await dispatch('fetchGames')
            return true
        },

        // 排行榜
        async fetchLeaderboard({ commit }) {
            const response = await axios.get('leaderboard/')
            commit('setLeaderboard', response.data)
            return response.data
        },

        // 获取预设策略
        async fetchPresetStrategies({ commit }) {
            try {
                const response = await axios.get('preset-strategies/')
                return response.data
            } catch (error) {
                handleApiError(commit, error)
                return []
            }
        },

        // 获取已删除的预设策略
        async fetchDeletedPresetStrategies({ commit }) {
            try {
                // 直接从API获取已删除的预设策略
                const response = await axios.get('deleted-preset-strategies/');
                return response.data;
            } catch (error) {
                handleApiError(commit, error);
                return [];
            }
        },

        // 添加锦标赛相关的actions
        async fetchTournaments({ commit }) {
            const response = await axios.get('tournaments/')
            commit('setTournaments', response.data)
            return response.data
        },

        async fetchTournament({ commit }, id) {
            try {
                // 创建一个可以被取消的请求
                const controller = new AbortController();
                const signal = controller.signal;

                // 设置超时，避免请求挂起
                const timeout = setTimeout(() => {
                    controller.abort();
                }, 10000); // 10秒超时

                try {
                    // 使用新的更可靠的API端点
                    const response = await axios.get(`tournaments/${id}/details/`, { signal });
                    clearTimeout(timeout);
                    commit('setCurrentTournament', response.data);
                    return response.data;
                } catch (innerError) {
                    clearTimeout(timeout);

                    // 检查是否是超时错误
                    if (innerError.name === 'AbortError') {
                        throw new Error('获取锦标赛详情超时，请检查网络连接并重试');
                    }

                    // 如果新API失败，尝试使用旧API作为备选
                    try {
                        console.log('尝试使用备选API获取锦标赛详情...');
                        const backupResponse = await axios.get(`tournaments/${id}/`);
                        commit('setCurrentTournament', backupResponse.data);
                        return backupResponse.data;
                    } catch (backupError) {
                        console.error('备选API也失败:', backupError);

                        // 处理错误
                        if (innerError.response && innerError.response.data && innerError.response.data.error) {
                            throw new Error(innerError.response.data.error);
                        } else if (innerError.response && innerError.response.status === 404) {
                            throw new Error('找不到指定的锦标赛');
                        } else {
                            throw innerError;
                        }
                    }
                }
            } catch (error) {
                console.error('获取锦标赛详情失败:', error);
                // 如果服务器返回了错误信息，使用服务器提供的错误信息
                if (error.response && error.response.data && error.response.data.error) {
                    throw new Error(error.response.data.error);
                } else {
                    throw new Error(error.message || '获取锦标赛详情失败，请重试');
                }
            }
        },

        async createTournament({ dispatch }, tournamentData) {
            const response = await axios.post('tournaments/create_tournament/', tournamentData)
            await dispatch('fetchTournaments')
            return response.data
        },

        async addParticipant({ dispatch }, { tournamentId, strategyId }) {
            const response = await axios.post(`tournaments/${tournamentId}/add_participant/`, {
                strategy_id: strategyId
            })
            await dispatch('fetchTournament', tournamentId)
            return response.data
        },

        async getTournamentParticipants({ commit }, tournamentId) {
            const response = await axios.get(`tournaments/${tournamentId}/get_participants/`)
            commit('setTournamentParticipants', response.data)
            return response.data
        },

        async startTournament({ commit }, tournamentId) {
            const response = await axios.post(`tournaments/${tournamentId}/start_tournament/`)
            commit('updateCurrentTournament', { status: 'IN_PROGRESS' })
            return response.data
        },

        async runTournament({ commit }, tournamentId) {
            const response = await axios.post(`tournaments/${tournamentId}/run_tournament/`)
            commit('updateCurrentTournament', { status: 'COMPLETED' })
            return response.data
        },

        async getTournamentResults({ commit }, tournamentId) {
            try {
                console.log('开始获取锦标赛结果，ID:', tournamentId)
                console.log('API请求URL:', `tournaments/${tournamentId}/results/`)

                const response = await axios.get(`tournaments/${tournamentId}/results/`)

                console.log('锦标赛结果API响应:', response)
                console.log('锦标赛结果数据:', response.data)

                // 检查响应中是否有有效的tournament数据
                if (!response.data || !response.data.id) {
                    console.error('API响应中没有有效的锦标赛数据')
                    throw new Error('API返回的锦标赛数据无效')
                }

                commit('setCurrentTournament', response.data)
                return response.data
            } catch (error) {
                console.error('获取锦标赛结果失败:', error)
                console.error('错误详情:', {
                    message: error.message,
                    status: error.response?.status,
                    statusText: error.response?.statusText,
                    responseData: error.response?.data
                })

                // 处理404或其他服务器错误
                if (error.response) {
                    if (error.response.status === 404) {
                        throw new Error('无法加载锦标赛数据，请确认锦标赛是否存在')
                    } else if (error.response.data && error.response.data.error) {
                        throw new Error(error.response.data.error)
                    }
                }

                // 处理网络错误或其他异常
                throw new Error(error.message || '获取锦标赛结果失败，请重试')
            }
        },

        // 删除锦标赛
        async deleteTournament({ dispatch }, tournamentId) {
            try {
                await axios.delete(`tournaments/${tournamentId}/delete_tournament/`)
                // 删除锦标赛后刷新列表
                await dispatch('fetchTournaments')
                return true
            } catch (error) {
                console.error('删除锦标赛失败:', error)
                // 将错误向上传播，以便组件可以处理
                throw error
            }
        }
    }
}) 