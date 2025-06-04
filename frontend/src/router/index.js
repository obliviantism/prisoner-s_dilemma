import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import StrategyList from '../views/StrategyList.vue'
import StrategyForm from '../views/StrategyForm.vue'
import GameList from '../views/GameList.vue'
import GameForm from '../views/GameForm.vue'
import GameDetail from '../views/GameDetail.vue'
import Leaderboard from '../views/Leaderboard.vue'
import History from '../views/History.vue'
import TournamentList from '../views/TournamentList.vue'
import TournamentForm from '../views/TournamentForm.vue'
import TournamentDetail from '../views/TournamentDetail.vue'
import TournamentResults from '../views/TournamentResults.vue'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: Home
    },
    {
        path: '/login',
        name: 'Login',
        component: Login
    },
    {
        path: '/register',
        name: 'Register',
        component: Register
    },
    {
        path: '/strategies',
        name: 'StrategyList',
        component: StrategyList,
        meta: { requiresAuth: true }
    },
    {
        path: '/strategies/create',
        name: 'StrategyCreate',
        component: StrategyForm,
        meta: { requiresAuth: true }
    },
    {
        path: '/strategies/:id/edit',
        name: 'StrategyEdit',
        component: StrategyForm,
        meta: { requiresAuth: true }
    },
    {
        path: '/games',
        name: 'GameList',
        component: GameList,
        meta: { requiresAuth: true }
    },
    {
        path: '/games/create',
        name: 'GameCreate',
        component: GameForm,
        meta: { requiresAuth: true }
    },
    {
        path: '/games/:id',
        name: 'GameDetail',
        component: GameDetail,
        meta: { requiresAuth: true }
    },
    {
        path: '/leaderboard',
        name: 'Leaderboard',
        component: Leaderboard,
        meta: { requiresAuth: true }
    },
    {
        path: '/history',
        name: 'History',
        component: History,
        meta: { requiresAuth: true }
    },
    {
        path: '/tournaments',
        name: 'TournamentList',
        component: TournamentList,
        meta: { requiresAuth: true }
    },
    {
        path: '/tournaments/create',
        name: 'TournamentCreate',
        component: TournamentForm,
        meta: { requiresAuth: true }
    },
    {
        path: '/tournaments/:id',
        name: 'TournamentDetail',
        component: TournamentDetail,
        meta: { requiresAuth: true }
    },
    {
        path: '/tournaments/:id/results',
        name: 'TournamentResults',
        component: TournamentResults,
        meta: { requiresAuth: true }
    }
]

const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes
})

// 导航守卫
router.beforeEach((to, from, next) => {
    const isAuthenticated = localStorage.getItem('token') !== null

    if (to.matched.some(record => record.meta.requiresAuth) && !isAuthenticated) {
        next({ name: 'Login', query: { redirect: to.fullPath } })
    } else {
        next()
    }
})

export default router 