from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

router = DefaultRouter()
router.register(r'strategies', views.StrategyViewSet, basename='api-strategy')
router.register(r'games', views.GameViewSet, basename='api-game')

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),
    path('api/auth/login/', obtain_auth_token, name='api-token-auth'),
    path('api/leaderboard/', views.api_leaderboard, name='api-leaderboard'),
    
    # Template URLs
    path('', views.home, name='home'),
    path('strategies/', views.StrategyListView.as_view(), name='strategy_list'),
    path('strategies/create/', views.StrategyCreateView.as_view(), name='strategy_create'),
    path('strategies/<int:pk>/edit/', views.StrategyUpdateView.as_view(), name='strategy_edit'),
    path('games/', views.GameListView.as_view(), name='game_list'),
    path('games/create/', views.game_create, name='game_create'),
    path('games/<int:pk>/', views.GameDetailView.as_view(), name='game_detail'),
    path('games/<int:pk>/play-round/', views.play_round, name='play_round'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
]