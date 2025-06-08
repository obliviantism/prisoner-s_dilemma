from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    StrategyViewSet, GameViewSet, home, 
    StrategyListView, StrategyCreateView, StrategyUpdateView,
    GameDetailView, GameListView, register_user, api_leaderboard, game_create, play_round, leaderboard,
    current_user, delete_game, TournamentViewSet, tournament_list, tournament_create, tournament_detail,
    tournament_add_participant, tournament_start, tournament_run, tournament_results, api_preset_strategies,
    tournament_detail_api, recalculate_tournament_stats, api_deleted_preset_strategies, fix_tournaments,
    emergency_fix_tournaments, reset_all_tournaments, visualize_q_learning_results, q_learning_curve, q_value_heatmap,
    q_learning_vs_opponents, export_tournament_results, debug_q_learning_tournament
)

# Register API URLs
router = DefaultRouter()
router.register(r'strategies', StrategyViewSet, basename='api-strategy')
router.register(r'games', GameViewSet, basename='api-game')
router.register(r'tournaments', TournamentViewSet, basename='api-tournament')

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    path('api/auth/login/', obtain_auth_token, name='api-token-auth'),
    path('api/auth/register/', register_user, name='api-register'),
    path('api/auth/user/', current_user, name='api-current-user'),
    path('api/leaderboard/', api_leaderboard, name='api-leaderboard'),
    path('api/preset-strategies/', api_preset_strategies, name='api-preset-strategies'),
    path('api/deleted-preset-strategies/', api_deleted_preset_strategies, name='api-deleted-preset-strategies'),
    path('api/tournaments/<int:pk>/details/', tournament_detail_api, name='api-tournament-detail'),
    
    # Template URLs
    path('', home, name='home'),
    path('strategies/', StrategyListView.as_view(), name='strategy_list'),
    path('strategies/create/', StrategyCreateView.as_view(), name='strategy_create'),
    path('strategies/<int:pk>/edit/', StrategyUpdateView.as_view(), name='strategy_edit'),
    path('games/', GameListView.as_view(), name='game_list'),
    path('games/create/', game_create, name='game_create'),
    path('games/<int:pk>/', GameDetailView.as_view(), name='game_detail'),
    path('games/<int:pk>/play-round/', play_round, name='play_round'),
    path('games/<int:pk>/delete/', delete_game, name='delete_game'),
    path('leaderboard/', leaderboard, name='leaderboard'),
    
    # 锦标赛相关URLs
    path('tournaments/', tournament_list, name='tournament_list'),
    path('tournaments/create/', tournament_create, name='tournament_create'),
    path('tournaments/<int:pk>/', tournament_detail, name='tournament_detail'),
    path('tournaments/<int:pk>/add-participant/', tournament_add_participant, name='tournament_add_participant'),
    path('tournaments/<int:pk>/start/', tournament_start, name='tournament_start'),
    path('tournaments/<int:pk>/run/', tournament_run, name='tournament_run'),
    path('tournaments/<int:tournament_id>/results/', tournament_results, name='tournament_results'),
    path('tournaments/<int:tournament_id>/export/', export_tournament_results, name='export_tournament_results'),
    
    # Q-learning结果可视化
    path('tournaments/<int:tournament_id>/q_learning/', visualize_q_learning_results, name='q_learning_results'),
    path('tournaments/<int:tournament_id>/q_learning/curve/', q_learning_curve, name='q_learning_curve'),
    path('tournaments/<int:tournament_id>/q_learning/heatmap/', q_value_heatmap, name='q_value_heatmap'),
    path('tournaments/<int:tournament_id>/q_learning/vs_opponents/', q_learning_vs_opponents, name='q_learning_vs_opponents'),
    
    # 调试URL
    path('tournaments/<int:tournament_id>/debug/', debug_q_learning_tournament, name='debug_q_learning_tournament'),
]