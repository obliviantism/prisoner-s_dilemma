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
from .models import Strategy, Game, Round, Tournament, TournamentParticipant, TournamentMatch
from .services import GameService, TournamentService
from .serializers import StrategySerializer, GameSerializer, TournamentSerializer
from django.db import connection

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
        
        try:
            game = GameService.create_game(strategy1, strategy2, total_rounds)
            serializer = self.get_serializer(game)
            return Response(serializer.data)
        except Exception as e:
            return Response({
                'error': f'创建游戏失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
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
    
    @action(detail=True, methods=['delete'])
    def delete_game(self, request, pk=None):
        game = self.get_object()
        
        # 保存删除前的游戏信息，用于响应消息
        game_info = {
            'id': game.id,
            'strategy1': game.strategy1.name,
            'strategy2': game.strategy2.name,
            'status': game.status,
            'player1_score': game.player1_score,
            'player2_score': game.player2_score
        }
        
        # 执行删除操作
        game.delete()
        
        # 重置ID自增计数器
        with connection.cursor() as cursor:
            # SQLite specific SQL to reset auto-increment
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='dilemma_game_game';")
        
        # 返回删除结果
        return Response({
            'message': f'Game {game_info["id"]} between {game_info["strategy1"]} and {game_info["strategy2"]} was successfully deleted',
            'deleted_game': game_info
        }, status=status.HTTP_200_OK)
        
    def destroy(self, request, *args, **kwargs):
        game = self.get_object()
        
        # 保存删除前的游戏信息，用于响应消息
        game_info = {
            'id': game.id,
            'strategy1': game.strategy1.name,
            'strategy2': game.strategy2.name,
            'status': game.status,
            'player1_score': game.player1_score,
            'player2_score': game.player2_score
        }
        
        # 执行删除操作
        self.perform_destroy(game)
        
        # 重置ID自增计数器
        with connection.cursor() as cursor:
            # SQLite specific SQL to reset auto-increment
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='dilemma_game_game';")
        
        # 返回删除结果
        return Response({
            'message': f'Game {game_info["id"]} between {game_info["strategy1"]} and {game_info["strategy2"]} was successfully deleted',
            'deleted_game': game_info
        }, status=status.HTTP_200_OK)

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
        
        try:
            game = GameService.create_game(strategy1, strategy2, total_rounds)
            messages.success(request, '游戏创建成功！')
            return redirect('game_detail', pk=game.id)
        except Exception as e:
            messages.error(request, f'创建游戏失败: {str(e)}')
            strategies = Strategy.objects.filter(created_by=request.user)
            return render(request, 'dilemma_game/game_form.html', {
                'strategies': strategies
            })
    
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
def delete_game(request, pk):
    game = get_object_or_404(Game, pk=pk)
    
    if request.method == 'POST':
        game_name = f"Game #{game.id}: {game.strategy1.name} vs {game.strategy2.name}"
        game.delete()
        
        # 重置ID自增计数器
        with connection.cursor() as cursor:
            # SQLite specific SQL to reset auto-increment
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='dilemma_game_game';")
            
        messages.success(request, f'{game_name} was successfully deleted.')
        return redirect('game_list')
    
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

# 添加锦标赛相关视图

class TournamentViewSet(viewsets.ModelViewSet):
    """
    锦标赛API视图集
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TournamentSerializer
    
    def get_queryset(self):
        return Tournament.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_tournament(self, request):
        """创建新的锦标赛"""
        name = request.data.get('name')
        description = request.data.get('description', '')
        rounds_per_match = int(request.data.get('rounds_per_match', 200))
        repetitions = int(request.data.get('repetitions', 5))
        
        # 检查自定义收益矩阵
        payoff_matrix = None
        if 'payoff_matrix' in request.data:
            try:
                payoff_matrix = request.data.get('payoff_matrix')
            except Exception as e:
                return Response({'error': f'Invalid payoff matrix format: {str(e)}'}, 
                               status=status.HTTP_400_BAD_REQUEST)
        
        try:
            tournament = TournamentService.create_tournament(
                name=name,
                description=description,
                user=request.user,
                rounds_per_match=rounds_per_match,
                repetitions=repetitions,
                payoff_matrix=payoff_matrix
            )
            
            return Response({
                'id': tournament.id,
                'name': tournament.name,
                'status': tournament.status,
                'message': 'Tournament created successfully'
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """添加参赛者到锦标赛"""
        tournament = self.get_object()
        strategy_id = request.data.get('strategy_id')
        
        try:
            strategy = Strategy.objects.get(id=strategy_id)
            participant = TournamentService.add_participant(tournament, strategy)
            
            return Response({
                'id': participant.id,
                'strategy_name': strategy.name,
                'message': f'Strategy {strategy.name} added to tournament'
            }, status=status.HTTP_201_CREATED)
        
        except Strategy.DoesNotExist:
            return Response({'error': 'Strategy not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def get_participants(self, request, pk=None):
        """获取锦标赛的所有参赛者"""
        tournament = self.get_object()
        participants = TournamentParticipant.objects.filter(tournament=tournament)
        
        result = []
        for p in participants:
            result.append({
                'id': p.id,
                'strategy_id': p.strategy.id,
                'strategy_name': p.strategy.name,
                'rank': p.rank,
                'total_score': p.total_score,
                'average_score': p.average_score
            })
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def start_tournament(self, request, pk=None):
        """开始锦标赛，生成所有比赛"""
        tournament = self.get_object()
        
        try:
            matches = TournamentService.generate_matches(tournament)
            
            return Response({
                'tournament_id': tournament.id,
                'status': tournament.status,
                'matches_count': len(matches),
                'message': 'Tournament started successfully'
            })
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def run_tournament(self, request, pk=None):
        """运行整个锦标赛，执行所有比赛"""
        tournament = self.get_object()
        
        try:
            results = TournamentService.run_tournament(tournament)
            
            return Response({
                'tournament_id': tournament.id,
                'status': tournament.status,
                'message': 'Tournament completed successfully',
                'results': results
            })
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """获取锦标赛结果"""
        tournament = self.get_object()
        
        if tournament.status != 'COMPLETED':
            return Response({
                'error': 'Tournament is not completed yet',
                'status': tournament.status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            results = TournamentService.get_tournament_results(tournament)
            return Response(results)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# 添加锦标赛的模板视图

@login_required
def tournament_list(request):
    tournaments = Tournament.objects.all().order_by('-created_at')
    return render(request, 'dilemma_game/tournament_list.html', {
        'tournaments': tournaments
    })

@login_required
def tournament_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        rounds_per_match = int(request.POST.get('rounds_per_match', 200))
        repetitions = int(request.POST.get('repetitions', 5))
        
        # 处理收益矩阵
        try:
            cc_reward = request.POST.getlist('cc_reward')
            cd_reward = request.POST.getlist('cd_reward')
            dc_reward = request.POST.getlist('dc_reward')
            dd_reward = request.POST.getlist('dd_reward')
            
            payoff_matrix = {
                'CC': [float(cc_reward[0]), float(cc_reward[1])],
                'CD': [float(cd_reward[0]), float(cd_reward[1])],
                'DC': [float(dc_reward[0]), float(dc_reward[1])],
                'DD': [float(dd_reward[0]), float(dd_reward[1])]
            }
        except (IndexError, ValueError):
            # 使用默认收益矩阵
            payoff_matrix = None
        
        tournament = TournamentService.create_tournament(
            name=name,
            description=description,
            user=request.user,
            rounds_per_match=rounds_per_match,
            repetitions=repetitions,
            payoff_matrix=payoff_matrix
        )
        
        messages.success(request, 'Tournament created successfully!')
        return redirect('tournament_detail', pk=tournament.id)
    
    return render(request, 'dilemma_game/tournament_form.html')

@login_required
def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    participants = TournamentParticipant.objects.filter(tournament=tournament).order_by('rank')
    
    return render(request, 'dilemma_game/tournament_detail.html', {
        'tournament': tournament,
        'participants': participants
    })

@login_required
def tournament_add_participant(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    
    if request.method == 'POST':
        strategy_ids = request.POST.getlist('strategy_ids')
        added_count = 0
        
        for strategy_id in strategy_ids:
            try:
                strategy = Strategy.objects.get(id=strategy_id)
                TournamentService.add_participant(tournament, strategy)
                added_count += 1
            except Exception as e:
                messages.error(request, f"Error adding strategy {strategy_id}: {str(e)}")
        
        if added_count > 0:
            messages.success(request, f'Added {added_count} strategies to the tournament.')
        
        return redirect('tournament_detail', pk=tournament.id)
    
    # 获取可用的策略
    available_strategies = Strategy.objects.filter(created_by=request.user)
    
    # 排除已添加的策略
    existing_strategies = TournamentParticipant.objects.filter(tournament=tournament).values_list('strategy_id', flat=True)
    available_strategies = available_strategies.exclude(id__in=existing_strategies)
    
    return render(request, 'dilemma_game/tournament_add_participant.html', {
        'tournament': tournament,
        'available_strategies': available_strategies
    })

@login_required
def tournament_start(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    
    try:
        TournamentService.generate_matches(tournament)
        messages.success(request, 'Tournament started successfully!')
    except Exception as e:
        messages.error(request, f'Error starting tournament: {str(e)}')
    
    return redirect('tournament_detail', pk=tournament.id)

@login_required
def tournament_run(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    
    try:
        TournamentService.run_tournament(tournament)
        messages.success(request, 'Tournament completed successfully!')
    except Exception as e:
        messages.error(request, f'Error running tournament: {str(e)}')
    
    return redirect('tournament_detail', pk=tournament.id)

@login_required
def tournament_results(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    
    if tournament.status != 'COMPLETED':
        messages.error(request, 'Tournament is not completed yet.')
        return redirect('tournament_detail', pk=tournament.id)
    
    participants = TournamentParticipant.objects.filter(tournament=tournament).order_by('rank')
    
    return render(request, 'dilemma_game/tournament_results.html', {
        'tournament': tournament,
        'participants': participants
    })
