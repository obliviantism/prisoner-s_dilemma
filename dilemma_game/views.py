from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import Strategy, Game, Round
from .services import GameService
from .serializers import StrategySerializer, GameSerializer

# Create your views here.

# API Views
class StrategyViewSet(viewsets.ModelViewSet):
    serializer_class = StrategySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Strategy.objects.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class GameViewSet(viewsets.ModelViewSet):
    serializer_class = GameSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Game.objects.all()
    
    @action(detail=False, methods=['post'])
    def start_game(self, request):
        strategy1_id = request.data.get('strategy1')
        strategy2_id = request.data.get('strategy2')
        total_rounds = request.data.get('total_rounds', 200)
        
        strategy1 = get_object_or_404(Strategy, id=strategy1_id)
        strategy2 = get_object_or_404(Strategy, id=strategy2_id)
        
        game = GameService.create_game(strategy1, strategy2, total_rounds)
        serializer = self.get_serializer(game)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def play_round(self, request, pk=None):
        game = self.get_object()
        try:
            GameService.play_round(game)
            serializer = self.get_serializer(game)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def play_full_game(self, request, pk=None):
        game = self.get_object()
        try:
            while game.current_round < game.total_rounds:
                GameService.play_round(game)
            serializer = self.get_serializer(game)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Template Views
@login_required
def home(request):
    recent_games = Game.objects.order_by('-created_at')[:5]
    return render(request, 'dilemma_game/home.html', {
        'recent_games': recent_games
    })

class StrategyListView(LoginRequiredMixin, ListView):
    model = Strategy
    template_name = 'dilemma_game/strategy_list.html'
    context_object_name = 'strategies'

    def get_queryset(self):
        return Strategy.objects.filter(created_by=self.request.user)

class StrategyCreateView(LoginRequiredMixin, CreateView):
    model = Strategy
    template_name = 'dilemma_game/strategy_form.html'
    fields = ['name', 'description', 'code']
    success_url = reverse_lazy('strategy_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Strategy created successfully!')
        return super().form_valid(form)

class StrategyUpdateView(LoginRequiredMixin, UpdateView):
    model = Strategy
    template_name = 'dilemma_game/strategy_form.html'
    fields = ['name', 'description', 'code']
    success_url = reverse_lazy('strategy_list')

    def get_queryset(self):
        return Strategy.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Strategy updated successfully!')
        return super().form_valid(form)

class GameListView(LoginRequiredMixin, ListView):
    model = Game
    template_name = 'dilemma_game/game_list.html'
    context_object_name = 'games'
    ordering = ['-created_at']

class GameDetailView(LoginRequiredMixin, DetailView):
    model = Game
    template_name = 'dilemma_game/game_detail.html'
    context_object_name = 'game'

@login_required
def game_create(request):
    if request.method == 'POST':
        strategy1_id = request.POST.get('strategy1')
        strategy2_id = request.POST.get('strategy2')
        total_rounds = int(request.POST.get('total_rounds', 200))
        
        strategy1 = get_object_or_404(Strategy, id=strategy1_id)
        strategy2 = get_object_or_404(Strategy, id=strategy2_id)
        
        game = GameService.create_game(strategy1, strategy2, total_rounds)
        messages.success(request, 'Game created successfully!')
        return redirect('game_detail', pk=game.id)
    
    strategies = Strategy.objects.filter(created_by=request.user)
    return render(request, 'dilemma_game/game_form.html', {
        'strategies': strategies
    })

@login_required
def play_round(request, pk):
    game = get_object_or_404(Game, pk=pk)
    
    if game.status == 'COMPLETED':
        messages.error(request, 'This game has already been completed.')
        return redirect('game_detail', pk=game.id)
    
    try:
        GameService.play_round(game)
        messages.success(request, 'Round played successfully!')
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('game_detail', pk=game.id)

@login_required
def leaderboard(request):
    strategies = Strategy.objects.all()
    strategy_stats = []
    
    for strategy in strategies:
        games_as_p1 = Game.objects.filter(strategy1=strategy, status='COMPLETED')
        games_as_p2 = Game.objects.filter(strategy2=strategy, status='COMPLETED')
        
        total_score = sum(g.player1_score for g in games_as_p1) + sum(g.player2_score for g in games_as_p2)
        total_games = games_as_p1.count() + games_as_p2.count()
        
        if total_games > 0:
            avg_score = total_score / total_games
        else:
            avg_score = 0
            
        strategy_stats.append({
            'strategy': strategy,
            'total_games': total_games,
            'total_score': total_score,
            'avg_score': avg_score
        })
    
    strategy_stats.sort(key=lambda x: x['avg_score'], reverse=True)
    
    return render(request, 'dilemma_game/leaderboard.html', {
        'strategy_stats': strategy_stats
    })

# API视图
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def api_leaderboard(request):
    strategies = Strategy.objects.all()
    strategy_stats = []
    
    for strategy in strategies:
        games_as_p1 = Game.objects.filter(strategy1=strategy, status='COMPLETED')
        games_as_p2 = Game.objects.filter(strategy2=strategy, status='COMPLETED')
        
        total_score = sum(g.player1_score for g in games_as_p1) + sum(g.player2_score for g in games_as_p2)
        total_games = games_as_p1.count() + games_as_p2.count()
        
        if total_games > 0:
            avg_score = total_score / total_games
        else:
            avg_score = 0
            
        strategy_stats.append({
            'strategy_id': strategy.id,
            'strategy_name': strategy.name,
            'created_by': strategy.created_by.username,
            'total_games': total_games,
            'total_score': total_score,
            'avg_score': avg_score
        })
    
    strategy_stats.sort(key=lambda x: x['avg_score'], reverse=True)
    
    return Response(strategy_stats)

# 获取当前用户API
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """
    获取当前登录用户的信息
    """
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email
    })

# 用户注册API
@api_view(['POST'])
def register_user(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': '用户名和密码是必须的'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)
    
    if email and User.objects.filter(email=email).exists():
        return Response({'error': '该邮箱已被注册'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, email=email, password=password)
    token = Token.objects.create(user=user)
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'message': '注册成功'
    }, status=status.HTTP_201_CREATED)
