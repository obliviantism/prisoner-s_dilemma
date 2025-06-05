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
from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Avg, Sum, F, FloatField, ExpressionWrapper, Q
import json
import random
import math
import time
import numpy as np
from collections import defaultdict
import logging
# 导入策略模块
from .strategies import get_all_strategies
from rest_framework import serializers

# 设置日志记录器
logger = logging.getLogger(__name__)

# Create your views here.

# API Views
class StrategyViewSet(viewsets.ModelViewSet):
    serializer_class = StrategySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Strategy.objects.filter(created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """重写create方法，添加更多错误处理"""
        try:
            # 记录创建请求
            strategy_name = request.data.get('name', '未命名')
            logger.info(f"用户 {request.user.username} 请求创建策略: {strategy_name}")
            
            # 调用父类的create方法
            response = super().create(request, *args, **kwargs)
            return response
        except serializers.ValidationError as e:
            # 记录验证错误，但保持原始错误响应
            logger.warning(f"策略 '{strategy_name}' 创建验证错误: {str(e)}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # 记录任何其他异常
            logger.error(f"创建策略 '{strategy_name}' 时出错: {str(e)}", exc_info=True)
            return Response(
                {'error': f'创建策略失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        # 检查是否是预设策略
        preset_id = self.request.data.get('preset_id')
        is_preset = bool(preset_id)
        
        try:
            # 记录正在尝试创建的策略
            strategy_name = self.request.data.get('name', '未命名')
            logger.info(f"正在创建策略: {strategy_name}, 预设ID: {preset_id if is_preset else '非预设'}")
            
            # 检查是否已存在相同名称的策略
            user = self.request.user
            existing_strategy = Strategy.objects.filter(name=strategy_name, created_by=user).first()
            if existing_strategy:
                logger.warning(f"用户 {user.username} 尝试创建已存在的策略: {strategy_name}")
                # 不抛出异常，而是让serializer处理这个问题
            
            # 保存策略，并添加预设标记
            serializer.save(
                created_by=self.request.user,
                is_preset=is_preset,
                preset_id=preset_id
            )
            
            logger.info(f"策略创建成功: {strategy_name}")
        except Exception as e:
            logger.error(f"创建策略 '{strategy_name}' 时出错: {str(e)}", exc_info=True)
            raise
        
    def destroy(self, request, *args, **kwargs):
        strategy = self.get_object()
        
        # 保存删除前的策略信息，用于响应消息
        strategy_info = {
            'id': strategy.id,
            'name': strategy.name,
            'created_by': strategy.created_by.username
        }
        
        try:
            # 检查这个策略是否正在被游戏或锦标赛使用
            games_count = Game.objects.filter(
                models.Q(strategy1=strategy) | models.Q(strategy2=strategy)
            ).count()
            
            tournament_participants_count = TournamentParticipant.objects.filter(
                strategy=strategy
            ).count()
            
            if games_count > 0 or tournament_participants_count > 0:
                # 提供更具体的错误信息
                error_details = []
                if games_count > 0:
                    error_details.append(f"该策略正在被 {games_count} 个游戏引用")
                if tournament_participants_count > 0:
                    error_details.append(f"该策略正在被 {tournament_participants_count} 个锦标赛引用")
                
                error_message = "无法删除此策略，因为它正在被使用: " + "，".join(error_details)
                
                return Response({
                    'error': error_message
                }, status=status.HTTP_409_CONFLICT)
            
            # 执行删除操作
            self.perform_destroy(strategy)
            
            # 返回删除结果
            return Response({
                'message': f'策略 "{strategy_info["name"]}" 已成功删除',
                'deleted_strategy': strategy_info
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"删除策略时出错: {e}", exc_info=True)
            return Response({
                'error': f'删除策略失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

# 添加预设策略的API
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def api_preset_strategies(request):
    """
    返回预设策略的列表
    现在使用策略模块中的数据
    """
    # 从策略模块获取所有预设策略
    preset_strategies = get_all_strategies()
    
    # 返回策略列表，同时保持API兼容性
    return Response(preset_strategies)

# 获取已删除的预设策略
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def api_deleted_preset_strategies(request):
    """
    返回用户曾经添加但后来删除的预设策略列表
    """
    # 获取所有预设策略
    preset_strategies = get_all_strategies()
    
    # 获取用户当前的所有策略
    user_strategies = Strategy.objects.filter(created_by=request.user)
    
    # 找出已添加的预设策略的ID
    existing_preset_ids = set(
        user_strategies.filter(is_preset=True).values_list('preset_id', flat=True)
    )
    
    # 过滤出已删除的预设策略
    deleted_presets = [
        preset for preset in preset_strategies 
        if preset['id'] not in existing_preset_ids
    ]
    
    return Response(deleted_presets)

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
    
    def retrieve(self, request, pk=None):
        """获取单个锦标赛详情，添加错误处理"""
        try:
            tournament = self.get_object()
            serializer = self.get_serializer(tournament)
            return Response(serializer.data)
        except Tournament.DoesNotExist:
            return Response(
                {'error': '找不到指定的锦标赛'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"获取锦标赛详情错误: {str(e)}")  # 服务器日志记录错误
            return Response(
                {'error': '获取锦标赛详情失败，请重试'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'])
    def delete_tournament(self, request, pk=None):
        """删除锦标赛及所有相关数据"""
        tournament = self.get_object()
        
        # 验证权限 - 只有创建者可以删除
        if tournament.created_by != request.user:
            return Response(
                {'error': 'You do not have permission to delete this tournament'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            # 删除锦标赛相关的所有数据
            tournament_name = tournament.name
            tournament.delete()
            
            return Response(
                {'message': f'Tournament "{tournament_name}" has been successfully deleted'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to delete tournament: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def create_tournament(self, request):
        """创建新的锦标赛"""
        name = request.data.get('name')
        description = request.data.get('description', '')
        
        # 回合数设置 - 支持固定回合数或随机回合数范围
        use_random_rounds = request.data.get('use_random_rounds', False)
        
        if use_random_rounds:
            min_rounds = int(request.data.get('min_rounds', 100))
            max_rounds = int(request.data.get('max_rounds', 300))
            # 设置一个默认值，但在随机模式下不会使用
            rounds_per_match = 200
        else:
            rounds_per_match = int(request.data.get('rounds_per_match', 200))
            # 设置默认值，但在固定回合模式下不会使用
            min_rounds = 100
            max_rounds = 300
            
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
                payoff_matrix=payoff_matrix,
                use_random_rounds=use_random_rounds,
                min_rounds=min_rounds,
                max_rounds=max_rounds
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
                'average_score': p.average_score,
                'wins': p.wins,
                'draws': p.draws,
                'losses': p.losses
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
        try:
            tournament = self.get_object()
            
            # 记录调试信息
            print(f"获取锦标赛结果，ID: {pk}, 状态: {tournament.status}")
            
            if tournament.status != 'COMPLETED':
                print(f"锦标赛 {pk} 未完成，当前状态: {tournament.status}")
                return Response({
                    'error': f'Tournament is not completed yet. Current status: {tournament.status}',
                    'status': tournament.status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取并打印参赛者信息
            participants = list(tournament.participants.all())
            print(f"锦标赛 {pk} 有 {len(participants)} 个参赛者")
            
            try:
                # 获取结果
                results = TournamentService.get_tournament_results(tournament)
                
                # 增强返回的数据，添加参赛者完整信息
                participants_data = []
                for p in tournament.participants.all():
                    try:
                        participant_data = {
                            'id': p.id,
                            'rank': p.rank,
                            'total_score': p.total_score,
                            'average_score': p.average_score,
                            'wins': p.wins,
                            'draws': p.draws,
                            'losses': p.losses,
                        }
                        
                        # 添加策略信息
                        if hasattr(p, 'strategy') and p.strategy:
                            participant_data['strategy'] = {
                                'id': p.strategy.id,
                                'name': p.strategy.name,
                                'description': p.strategy.description
                            }
                        else:
                            participant_data['strategy'] = None
                            print(f"警告：参赛者 {p.id} 没有关联的策略")
                            
                        participants_data.append(participant_data)
                    except Exception as e:
                        print(f"处理参赛者 {p.id} 时出错: {str(e)}")
                
                # 替换原有的participants数据
                results['participants'] = participants_data
                
                # 确保id字段存在
                results['id'] = tournament.id
                
                # 打印结果摘要
                print(f"锦标赛结果包含字段: {', '.join(results.keys())}")
                print(f"matchups_matrix类型: {type(results.get('matchups_matrix'))}")
                
                return Response(results)
                
            except Exception as e:
                print(f"获取锦标赛 {pk} 结果时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"访问锦标赛 {pk} 时出错: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# 添加锦标赛的模板视图

@login_required
def tournament_list(request):
    try:
        tournaments = Tournament.objects.all().order_by('-created_at')
        
        # 检查锦标赛对象是否有异常
        valid_tournaments = []
        for tournament in tournaments:
            try:
                # 简单访问一些属性来检测是否有异常
                tournament_id = tournament.id
                tournament_name = tournament.name
                tournament_status = tournament.status
                
                # 尝试访问收益矩阵，这通常是出错的地方
                try:
                    matrix = tournament.payoff_matrix
                except Exception as e:
                    # 如果访问收益矩阵出错，记录但不中断
                    print(f"锦标赛 {tournament_id} 的收益矩阵访问出错: {str(e)}")
                    # 尝试修复收益矩阵
                    tournament.payoff_matrix_json = '{"CC":[3,3],"CD":[0,5],"DC":[5,0],"DD":[0,0]}'
                    tournament.save()
                
                # 通过测试，添加到有效列表中
                valid_tournaments.append(tournament)
            except Exception as e:
                # 如果锦标赛对象异常，跳过这个对象
                print(f"处理锦标赛对象时出错: {str(e)}")
                continue
        
        return render(request, 'dilemma_game/tournament_list.html', {
            'tournaments': valid_tournaments
        })
    except Exception as e:
        # 捕获整体视图函数的异常
        print(f"tournament_list视图出错: {str(e)}")
        from django.contrib import messages
        messages.error(request, f"获取锦标赛列表失败，请尝试修复功能: {str(e)}")
        return render(request, 'dilemma_game/tournament_list.html', {
            'error_message': f"获取锦标赛列表失败: {str(e)}",
            'tournaments': []
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
            # 使用新的表单字段名称获取收益矩阵值
            payoff_matrix = {
                'CC': [float(request.POST.get('cc_reward_p1', 3)), float(request.POST.get('cc_reward_p2', 3))],
                'CD': [float(request.POST.get('cd_reward_p1', 0)), float(request.POST.get('cd_reward_p2', 5))],
                'DC': [float(request.POST.get('dc_reward_p1', 5)), float(request.POST.get('dc_reward_p2', 0))],
                'DD': [float(request.POST.get('dd_reward_p1', 0)), float(request.POST.get('dd_reward_p2', 0))]
            }
            
            # 验证收益矩阵是否有效
            for key, values in payoff_matrix.items():
                if len(values) != 2 or not all(isinstance(v, (int, float)) for v in values):
                    raise ValueError(f"收益矩阵格式错误: {key}={values}")
            
        except ValueError as e:
            messages.error(request, f'收益矩阵设置错误: {str(e)}')
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
def tournament_results(request, tournament_id):
    """显示锦标赛结果"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if tournament.status != 'COMPLETED':
        messages.error(request, '锦标赛尚未完成。')
        return redirect('tournament_detail', pk=tournament.id)
    
    participants = TournamentParticipant.objects.filter(tournament=tournament).order_by('rank')
    
    # 确保每个参赛者的胜负平数据都已初始化
    for p in participants:
        # 打印调试信息
        print(f"参赛者 {p.strategy.name}: 胜={p.wins}, 平={p.draws}, 负={p.losses}")
        
        if p.wins is None or p.draws is None or p.losses is None:
            try:
                # 作为玩家1的比赛
                matches_as_p1 = TournamentMatch.objects.filter(
                    tournament=tournament,
                    participant1=p,
                    status='COMPLETED'
                )
                
                # 作为玩家2的比赛
                matches_as_p2 = TournamentMatch.objects.filter(
                    tournament=tournament,
                    participant2=p,
                    status='COMPLETED'
                )
                
                # 计算胜负平
                wins = 0
                losses = 0
                draws = 0
                
                # 作为玩家1的胜负平
                for match in matches_as_p1:
                    if match.player1_score > match.player2_score:
                        wins += 1
                    elif match.player1_score < match.player2_score:
                        losses += 1
                    else:
                        draws += 1
                
                # 作为玩家2的胜负平
                for match in matches_as_p2:
                    if match.player2_score > match.player1_score:
                        wins += 1
                    elif match.player2_score < match.player1_score:
                        losses += 1
                    else:
                        draws += 1
                
                # 更新参赛者的胜负平
                p.wins = wins
                p.draws = draws
                p.losses = losses
                p.save()
                
                print(f"已更新参赛者 {p.strategy.name}: 胜={p.wins}, 平={p.draws}, 负={p.losses}")
            except Exception as e:
                print(f"计算胜负平时出错: {str(e)}")
    
    # 刷新参赛者数据
    participants = TournamentParticipant.objects.filter(tournament=tournament).order_by('rank')
    
    context = {
        'tournament': tournament,
        'participants': participants
    }
    return render(request, 'dilemma_game/tournament_results.html', context)

# 添加专门的API视图函数获取锦标赛详情
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def tournament_detail_api(request, pk):
    """
    获取单个锦标赛的详细信息，包含完整的参赛者和比赛数据
    """
    try:
        tournament = get_object_or_404(Tournament, pk=pk)
        
        # 获取参赛者信息
        participants = []
        for p in TournamentParticipant.objects.filter(tournament=tournament):
            try:
                participants.append({
                    'id': p.id,
                    'strategy': {
                        'id': p.strategy.id,
                        'name': p.strategy.name,
                        'description': p.strategy.description
                    },
                    'total_score': p.total_score,
                    'average_score': p.average_score,
                    'rank': p.rank,
                    'wins': p.wins,
                    'draws': p.draws,
                    'losses': p.losses
                })
            except Exception as e:
                print(f"处理参赛者时出错 (id={p.id}): {str(e)}")
        
        # 获取比赛信息
        matches = []
        for m in TournamentMatch.objects.filter(tournament=tournament)[:10]:
            try:
                matches.append({
                    'id': m.id,
                    'participant1': {
                        'id': m.participant1.id,
                        'strategy_name': m.participant1.strategy.name
                    },
                    'participant2': {
                        'id': m.participant2.id,
                        'strategy_name': m.participant2.strategy.name
                    },
                    'repetition': m.repetition,
                    'player1_score': m.player1_score,
                    'player2_score': m.player2_score,
                    'status': m.status
                })
            except Exception as e:
                print(f"处理比赛时出错 (id={m.id}): {str(e)}")
        
        # 构建基本信息
        result = {
            'id': tournament.id,
            'name': tournament.name,
            'description': tournament.description,
            'created_by': tournament.created_by.id,
            'created_by_username': tournament.created_by.username,
            'rounds_per_match': tournament.rounds_per_match,
            'use_random_rounds': tournament.use_random_rounds,
            'min_rounds': tournament.min_rounds,
            'max_rounds': tournament.max_rounds,
            'repetitions': tournament.repetitions,
            'status': tournament.status,
            'created_at': tournament.created_at,
            'completed_at': tournament.completed_at,
            'payoff_matrix': tournament.payoff_matrix,
            'participants': participants,
            'matches': matches
        }
        
        return Response(result)
    
    except Tournament.DoesNotExist:
        return Response(
            {'error': '找不到指定的锦标赛'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"获取锦标赛详情API错误: {str(e)}")
        return Response(
            {'error': f'获取锦标赛详情失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@login_required
def recalculate_tournament_stats(request, tournament_id):
    """重新计算指定锦标赛的胜负平统计"""
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # 检查权限，只有创建者或管理员可以重新计算
    if request.user != tournament.created_by and not request.user.is_staff:
        messages.error(request, "您没有权限执行此操作")
        return redirect('tournament_detail', tournament_id=tournament_id)
    
    # 重新计算结果
    try:
        TournamentService.calculate_results(tournament)
        messages.success(request, "锦标赛胜负平统计已成功更新")
    except Exception as e:
        messages.error(request, f"更新失败: {str(e)}")
    
    # 重定向到结果页面
    return redirect('tournament_results', tournament_id=tournament_id)

@login_required
def fix_tournaments(request):
    """修复所有锦标赛记录，解决获取锦标赛列表失败的问题"""
    try:
        # 获取所有锦标赛
        tournaments = Tournament.objects.all()
        fixed_count = 0
        
        for tournament in tournaments:
            # 修复收益矩阵
            tournament.payoff_matrix_json = '{"CC":[3,3],"CD":[0,5],"DC":[5,0],"DD":[0,0]}'
            
            # 重置状态为CREATED
            tournament.status = 'CREATED'
            
            # 保存更改
            tournament.save()
            
            # 删除相关比赛
            TournamentMatch.objects.filter(tournament=tournament).delete()
            
            # 重置参赛者
            for participant in TournamentParticipant.objects.filter(tournament=tournament):
                participant.total_score = 0
                participant.average_score = 0
                participant.rank = None
                participant.wins = 0
                participant.draws = 0
                participant.losses = 0
                participant.save()
            
            fixed_count += 1
        
        messages.success(request, f'成功修复 {fixed_count} 个锦标赛记录')
        return redirect('tournament_list')
    except Exception as e:
        messages.error(request, f'修复锦标赛记录时出错: {str(e)}')
        return redirect('home')

@login_required
def emergency_fix_tournaments(request):
    """紧急修复所有锦标赛记录"""
    from django.contrib import messages
    from django.shortcuts import redirect
    
    try:
        # 获取所有锦标赛
        tournaments = Tournament.objects.all()
        fixed_count = 0
        deleted_count = 0
        
        for tournament in tournaments:
            try:
                # 检查是否有收益矩阵问题
                try:
                    matrix = tournament.payoff_matrix
                except Exception:
                    # 如果无法访问收益矩阵，则删除整个锦标赛
                    tournament_id = tournament.id
                    tournament_name = tournament.name
                    tournament.delete()
                    deleted_count += 1
                    print(f"删除了问题锦标赛 ID={tournament_id}, 名称='{tournament_name}'")
                    continue
                
                # 修复收益矩阵
                tournament.payoff_matrix_json = '{"CC":[3,3],"CD":[0,5],"DC":[5,0],"DD":[0,0]}'
                
                # 重置状态
                tournament.status = 'CREATED'
                
                # 保存更改
                tournament.save()
                
                # 删除相关比赛
                TournamentMatch.objects.filter(tournament=tournament).delete()
                
                # 重置参赛者
                for p in TournamentParticipant.objects.filter(tournament=tournament):
                    p.total_score = 0
                    p.average_score = 0
                    p.rank = None
                    p.wins = 0
                    p.draws = 0
                    p.losses = 0
                    p.save()
                
                fixed_count += 1
            except Exception as e:
                print(f"修复锦标赛 ID={tournament.id} 时出错: {str(e)}")
        
        if deleted_count > 0:
            messages.warning(request, f'删除了 {deleted_count} 个无法修复的锦标赛记录')
        
        if fixed_count > 0:
            messages.success(request, f'成功修复了 {fixed_count} 个锦标赛记录')
        else:
            messages.info(request, '没有需要修复的锦标赛记录')
        
        return redirect('tournament_list')
    
    except Exception as e:
        messages.error(request, f'修复锦标赛时出错: {str(e)}')
        return redirect('home')

@login_required
def reset_all_tournaments(request):
    """完全重置所有锦标赛记录 - 紧急情况下使用"""
    from django.contrib import messages
    from django.shortcuts import redirect
    
    try:
        # 删除所有锦标赛相关记录
        matches_count = TournamentMatch.objects.all().count()
        TournamentMatch.objects.all().delete()
        
        participants_count = TournamentParticipant.objects.all().count()
        TournamentParticipant.objects.all().delete()
        
        tournaments_count = Tournament.objects.all().count()
        Tournament.objects.all().delete()
        
        messages.success(
            request, 
            f'成功删除所有锦标赛数据: {tournaments_count} 个锦标赛, '
            f'{participants_count} 名参赛者, {matches_count} 场比赛'
        )
        return redirect('tournament_list')
    
    except Exception as e:
        messages.error(request, f'重置数据库出错: {str(e)}')
        return redirect('home')
