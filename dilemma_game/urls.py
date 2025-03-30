from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import (
    StrategyViewSet, GameViewSet, home, 
    StrategyListView, StrategyCreateView, StrategyUpdateView,
    GameDetailView, GameListView, register_user, api_leaderboard, game_create, play_round, leaderboard,
    current_user
)

# Register API URLs
router = DefaultRouter()
router.register(r'strategies', StrategyViewSet, basename='api-strategy')
router.register(r'games', GameViewSet, basename='api-game')

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    path('api/auth/login/', obtain_auth_token, name='api-token-auth'),
    path('api/auth/register/', register_user, name='api-register'),
    path('api/auth/user/', current_user, name='api-current-user'),
    path('api/leaderboard/', api_leaderboard, name='api-leaderboard'),
    
    # Template URLs
    path('', home, name='home'),
    path('strategies/', StrategyListView.as_view(), name='strategy_list'),
    path('strategies/create/', StrategyCreateView.as_view(), name='strategy_create'),
    path('strategies/<int:pk>/edit/', StrategyUpdateView.as_view(), name='strategy_edit'),
    path('games/', GameListView.as_view(), name='game_list'),
    path('games/create/', game_create, name='game_create'),
    path('games/<int:pk>/', GameDetailView.as_view(), name='game_detail'),
    path('games/<int:pk>/play-round/', play_round, name='play_round'),
    path('leaderboard/', leaderboard, name='leaderboard'),
]