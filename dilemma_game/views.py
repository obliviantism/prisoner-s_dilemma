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
import matplotlib
matplotlib.use('Agg')  # 设置为非交互式后端
import matplotlib.pyplot as plt
# 设置matplotlib中文字体支持
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei', 'Heiti TC', 'sans-serif']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

import io
import pickle
import os
from django.http import HttpResponse
from matplotlib.colors import LinearSegmentedColormap
import csv

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
        
        # 验证权限 - 创建者或管理员可以删除
        if tournament.created_by != request.user and not (request.user.is_staff or request.user.is_superuser):
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
        
        # 获取设置类型标志
        use_random_rounds = request.data.get('use_random_rounds', False)
        use_probability_model = request.data.get('use_probability_model', False)
        
        # 根据设置类型选择参数
        if use_probability_model:
            # 概率模型设置
            continue_probability = float(request.data.get('continue_probability', 0.95))
            # 设置默认值，但在概率模型下不会使用
            rounds_per_match = 200
            min_rounds = 100
            max_rounds = 300
        elif use_random_rounds:
            # 随机回合数设置
            min_rounds = int(request.data.get('min_rounds', 100))
            max_rounds = int(request.data.get('max_rounds', 300))
            # 设置默认值，但在随机模式下不会使用
            rounds_per_match = 200
            continue_probability = 0.95
        else:
            # 固定回合数设置
            rounds_per_match = int(request.data.get('rounds_per_match', 200))
            # 设置默认值，但在固定回合模式下不会使用
            min_rounds = 100
            max_rounds = 300
            continue_probability = 0.95
            
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
                max_rounds=max_rounds,
                use_probability_model=use_probability_model,
                continue_probability=continue_probability
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
            'use_probability_model': tournament.use_probability_model,
            'continue_probability': tournament.continue_probability,
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

# Q-learning可视化相关视图
def visualize_q_learning_results(request, tournament_id):
    """
    可视化Q-learning策略的学习结果
    
    参数:
        request: HTTP请求对象
        tournament_id: 锦标赛ID
    """
    # 获取锦标赛对象
    try:
        tournament = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        messages.error(request, "锦标赛不存在")
        return redirect('tournament_list')
    
    # 查找使用Q-learning策略的参与者
    try:
        q_learning_strategy = Strategy.objects.get(preset_id='q_learning')
        q_learning_participant = TournamentParticipant.objects.get(
            tournament=tournament,
            strategy=q_learning_strategy
        )
    except (Strategy.DoesNotExist, TournamentParticipant.DoesNotExist):
        messages.error(request, "该锦标赛中没有Q-learning策略参与者")
        return redirect('tournament_results', tournament_id=tournament_id)
    
    context = {
        'tournament': tournament,
        'participant': q_learning_participant
    }
    
    return render(request, 'dilemma_game/q_learning_results.html', context)

def q_learning_curve(request, tournament_id):
    """
    生成Q-learning策略的学习曲线图
    
    参数:
        request: HTTP请求对象
        tournament_id: 锦标赛ID
    """
    try:
        tournament = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        return HttpResponse("锦标赛不存在", status=404)
    
    # 查找使用Q-learning策略的参与者
    try:
        q_learning_strategy = Strategy.objects.get(preset_id='q_learning')
        q_learning_participant = TournamentParticipant.objects.get(
            tournament=tournament,
            strategy=q_learning_strategy
        )
    except (Strategy.DoesNotExist, TournamentParticipant.DoesNotExist):
        return HttpResponse("该锦标赛中没有Q-learning策略参与者", status=404)
    
    # 尝试加载特定锦标赛的学习数据
    model_dir = os.path.join('models')
    base_filename = 'q_learning_model.pkl'
    tournament_filename = f'q_learning_model_tournament_{tournament_id}.pkl'
    model_path = os.path.join(model_dir, tournament_filename)
    
    # 如果锦标赛特定的模型文件不存在，尝试使用全局模型文件
    if not os.path.exists(model_path):
        model_path = os.path.join(model_dir, base_filename)
        if not os.path.exists(model_path):
            return HttpResponse("找不到Q-Learning模型文件", status=404)
    
    try:
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
        
        # 检查数据结构，提取学习曲线数据
        if isinstance(data, dict) and 'learning_curve' in data:
            learning_curve = data['learning_curve']
        else:
            # 旧模型文件可能只包含Q表，创建模拟的学习曲线
            learning_curve = [3.0] * 10  # 占位数据
    except Exception as e:
        return HttpResponse(f"无法读取模型文件: {str(e)}", status=500)
    
    if not learning_curve:
        return HttpResponse("学习曲线数据为空", status=404)
    
    # 创建学习曲线数据
    rounds = list(range(1, len(learning_curve) + 1))
    scores = learning_curve
    
    # 计算移动平均分数，窗口大小为5
    window_size = min(5, len(scores))
    if window_size > 0:
        moving_avg = np.convolve(scores, np.ones(window_size)/window_size, mode='valid')
        moving_avg_rounds = rounds[window_size-1:]
    else:
        moving_avg = []
        moving_avg_rounds = []
    
    # 生成图表
    plt.figure(figsize=(10, 6))
    plt.plot(rounds, scores, 'o-', alpha=0.7, label='每场比赛得分')
    
    if len(moving_avg) > 1:
        plt.plot(moving_avg_rounds, moving_avg, 'r-', linewidth=2, label='移动平均')
    
    plt.title(f'锦标赛 #{tournament_id} Q-learning策略学习曲线', fontsize=14)
    plt.xlabel('回合数', fontsize=12)
    plt.ylabel('得分', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # 保存图表到内存
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=80)
    buffer.seek(0)
    plt.close()
    
    # 返回图表
    return HttpResponse(buffer.getvalue(), content_type='image/png')

def q_value_heatmap(request, tournament_id):
    """
    生成Q值热力图
    
    参数:
        request: HTTP请求对象
        tournament_id: 锦标赛ID
    """
    # 尝试加载特定锦标赛的Q表
    model_dir = os.path.join('models')
    base_filename = 'q_learning_model.pkl'
    tournament_filename = f'q_learning_model_tournament_{tournament_id}.pkl'
    model_path = os.path.join(model_dir, tournament_filename)
    
    # 如果锦标赛特定的模型文件不存在，尝试使用全局模型文件
    if not os.path.exists(model_path):
        model_path = os.path.join(model_dir, base_filename)
        if not os.path.exists(model_path):
            return HttpResponse("找不到Q表文件", status=404)
    
    try:
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
        
        # 检查数据结构，提取Q表
        if isinstance(data, dict) and 'q_table' in data:
            q_table = data['q_table']
        else:
            # 旧模型文件可能直接是Q表
            q_table = data
    except Exception as e:
        return HttpResponse(f"无法加载Q表: {str(e)}", status=500)
    
    if not q_table:
        return HttpResponse("Q表为空", status=404)
    
    # 筛选出有意义的状态（例如，排除全N的状态）
    meaningful_states = [state for state in q_table.keys() if 'N' not in state or (state.count('N') < len(state))]
    
    # 如果状态太多，只选择前20个
    if len(meaningful_states) > 20:
        meaningful_states = sorted(meaningful_states)[:20]
    
    # 生成热力图数据
    q_values_c = [q_table[state]['C'] for state in meaningful_states]
    q_values_d = [q_table[state]['D'] for state in meaningful_states]
    
    # 计算热力图的值范围
    min_q = min(min(q_values_c), min(q_values_d))
    max_q = max(max(q_values_c), max(q_values_d))
    
    # 创建热力图
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 创建数据矩阵
    data = np.array([q_values_c, q_values_d])
    
    # 定义自定义颜色映射：负值为红色，正值为绿色，零值为白色
    cmap = LinearSegmentedColormap.from_list(
        'RdWtGn', [(0.8, 0, 0), (1, 1, 1), (0, 0.8, 0)], N=100
    )
    
    # 绘制热力图
    im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=min_q, vmax=max_q)
    
    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Q值', fontsize=12)
    
    # 添加标签
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['合作', '背叛'])
    ax.set_xticks(range(len(meaningful_states)))
    ax.set_xticklabels(meaningful_states, rotation=90)
    
    # 在每个单元格中显示Q值
    for i in range(2):
        for j in range(len(meaningful_states)):
            text = ax.text(j, i, f"{data[i, j]:.2f}",
                          ha="center", va="center", color="black", fontsize=8)
    
    plt.title(f'锦标赛 #{tournament_id} Q-learning策略的状态-动作值热力图', fontsize=14)
    plt.tight_layout()
    
    # 保存图表到内存
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    plt.close()
    
    # 返回图表
    return HttpResponse(buffer.getvalue(), content_type='image/png')

def q_learning_vs_opponents(request, tournament_id):
    """
    生成Q-learning与各个对手的对战结果图表
    
    参数:
        request: HTTP请求对象
        tournament_id: 锦标赛ID
    """
    try:
        tournament = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        return HttpResponse("锦标赛不存在", status=404)
    
    # 查找使用Q-learning策略的参与者
    try:
        q_learning_strategy = Strategy.objects.get(preset_id='q_learning')
        q_learning_participant = TournamentParticipant.objects.get(
            tournament=tournament,
            strategy=q_learning_strategy
        )
    except (Strategy.DoesNotExist, TournamentParticipant.DoesNotExist):
        return HttpResponse("该锦标赛中没有Q-learning策略参与者", status=404)
    
    # 获取所有涉及Q-learning策略的比赛
    q_learning_matches = TournamentMatch.objects.filter(
        Q(participant1=q_learning_participant) | Q(participant2=q_learning_participant),
        tournament=tournament,
        status='COMPLETED'
    )
    
    # 按对手分组统计比赛结果
    opponent_results = {}
    
    for match in q_learning_matches:
        if match.participant1 == q_learning_participant:
            q_score = match.player1_score
            opp_score = match.player2_score
            opponent_name = match.participant2.strategy.name
        else:
            q_score = match.player2_score
            opp_score = match.player1_score
            opponent_name = match.participant1.strategy.name
        
        if opponent_name not in opponent_results:
            opponent_results[opponent_name] = {
                'q_scores': [],
                'opp_scores': [],
                'wins': 0,
                'draws': 0,
                'losses': 0
            }
        
        opponent_results[opponent_name]['q_scores'].append(q_score)
        opponent_results[opponent_name]['opp_scores'].append(opp_score)
        
        if q_score > opp_score:
            opponent_results[opponent_name]['wins'] += 1
        elif q_score < opp_score:
            opponent_results[opponent_name]['losses'] += 1
        else:
            opponent_results[opponent_name]['draws'] += 1
    
    # 计算平均分数
    for opponent in opponent_results:
        opponent_results[opponent]['avg_q_score'] = sum(opponent_results[opponent]['q_scores']) / len(opponent_results[opponent]['q_scores'])
        opponent_results[opponent]['avg_opp_score'] = sum(opponent_results[opponent]['opp_scores']) / len(opponent_results[opponent]['opp_scores'])
    
    # 按照Q-learning的平均分从高到低排序
    sorted_opponents = sorted(
        opponent_results.items(),
        key=lambda x: x[1]['avg_q_score'],
        reverse=True
    )
    
    # 准备作图数据
    opponents = [opp[0] for opp in sorted_opponents]
    q_scores = [opp[1]['avg_q_score'] for opp in sorted_opponents]
    opp_scores = [opp[1]['avg_opp_score'] for opp in sorted_opponents]
    
    # 准备胜负平数据
    wins = [opp[1]['wins'] for opp in sorted_opponents]
    draws = [opp[1]['draws'] for opp in sorted_opponents]
    losses = [opp[1]['losses'] for opp in sorted_opponents]
    
    # 创建双子图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
    
    # 设置柱状图的宽度
    bar_width = 0.35
    
    # 绘制平均得分对比
    x = np.arange(len(opponents))
    ax1.bar(x - bar_width/2, q_scores, bar_width, label='Q-learning', color='royalblue')
    ax1.bar(x + bar_width/2, opp_scores, bar_width, label='对手', color='lightcoral')
    
    # 设置标题和标签
    ax1.set_title(f'锦标赛 #{tournament_id} Q-learning与各对手平均得分对比', fontsize=14)
    ax1.set_xlabel('对手策略', fontsize=12)
    ax1.set_ylabel('平均得分', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(opponents, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 绘制胜负平统计
    bottom_draws = np.array(wins)
    bottom_losses = bottom_draws + np.array(draws)
    
    ax2.bar(opponents, wins, label='胜利', color='forestgreen')
    ax2.bar(opponents, draws, bottom=bottom_draws, label='平局', color='gold')
    ax2.bar(opponents, losses, bottom=bottom_losses, label='失败', color='firebrick')
    
    # 设置标题和标签
    ax2.set_title(f'锦标赛 #{tournament_id} Q-learning与各对手胜负平统计', fontsize=14)
    ax2.set_xlabel('对手策略', fontsize=12)
    ax2.set_ylabel('场次', fontsize=12)
    ax2.set_xticklabels(opponents, rotation=45, ha='right')
    ax2.legend()
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表到内存
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100)
    buffer.seek(0)
    plt.close()
    
    # 返回图表
    return HttpResponse(buffer.getvalue(), content_type='image/png')

@login_required
def export_tournament_results(request, tournament_id):
    """
    导出锦标赛结果为CSV文件
    
    参数:
        request: HTTP请求对象
        tournament_id: 锦标赛ID
    """
    try:
        tournament = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        messages.error(request, "锦标赛不存在")
        return redirect('tournament_list')
    
    # 获取参赛者数据，按排名排序
    participants = TournamentParticipant.objects.filter(
        tournament=tournament
    ).order_by('rank')
    
    # 创建CSV响应
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="tournament_{tournament_id}_results.csv"'
    
    # 使用UTF-8 BOM确保Excel正确显示中文
    response.write(u'\ufeff')
    
    writer = csv.writer(response)
    # 写入标题行
    writer.writerow(['锦标赛名称', tournament.name])
    writer.writerow(['描述', tournament.description])
    writer.writerow(['创建时间', tournament.created_at.strftime('%Y-%m-%d %H:%M')])
    writer.writerow(['完成时间', tournament.completed_at.strftime('%Y-%m-%d %H:%M') if tournament.completed_at else 'N/A'])
    writer.writerow([])  # 空行
    
    # 写入收益矩阵
    writer.writerow(['收益矩阵'])
    writer.writerow(['', '玩家2合作(C)', '玩家2背叛(D)'])
    writer.writerow(['玩家1合作(C)', 
                    f"{tournament.payoff_matrix['CC'][0]}, {tournament.payoff_matrix['CC'][1]}",
                    f"{tournament.payoff_matrix['CD'][0]}, {tournament.payoff_matrix['CD'][1]}"])
    writer.writerow(['玩家1背叛(D)', 
                    f"{tournament.payoff_matrix['DC'][0]}, {tournament.payoff_matrix['DC'][1]}",
                    f"{tournament.payoff_matrix['DD'][0]}, {tournament.payoff_matrix['DD'][1]}"])
    writer.writerow([])  # 空行
    
    # 写入参赛者结果
    writer.writerow(['排名', '策略名称', '总分', '平均分', '胜场数', '平局数', '负场数'])
    for participant in participants:
        strategy_name = participant.strategy.name.split('(')[0].strip()  # 取策略名称的第一部分
        writer.writerow([
            participant.rank,
            strategy_name,
            f"{participant.total_score:.1f}",
            f"{participant.average_score:.2f}",
            participant.wins,
            participant.draws,
            participant.losses
        ])
    
    # 如果有Q-learning策略，添加Q-learning模型的简要分析
    try:
        q_learning_strategy = Strategy.objects.get(preset_id='q_learning')
        q_learning_participant = TournamentParticipant.objects.filter(
            tournament=tournament,
            strategy=q_learning_strategy
        ).first()
        
        if q_learning_participant:
            writer.writerow([])  # 空行
            writer.writerow(['Q-learning策略分析'])
            writer.writerow(['排名', q_learning_participant.rank])
            writer.writerow(['总分', f"{q_learning_participant.total_score:.1f}"])
            writer.writerow(['平均分', f"{q_learning_participant.average_score:.2f}"])
            writer.writerow(['胜/平/负', f"{q_learning_participant.wins}/{q_learning_participant.draws}/{q_learning_participant.losses}"])
            
            # 如果存在模型文件，添加一些Q值信息
            model_path = os.path.join('models', 'q_learning_model.pkl')
            if os.path.exists(model_path):
                try:
                    with open(model_path, 'rb') as f:
                        q_table = pickle.load(f)
                    
                    # 选择一些典型状态的Q值
                    typical_states = ['CCC', 'CCD', 'CDC', 'CDD', 'DCC', 'DCD', 'DDC', 'DDD']
                    writer.writerow([])
                    writer.writerow(['典型状态Q值'])
                    writer.writerow(['状态', '合作(C)的Q值', '背叛(D)的Q值', '最优动作'])
                    
                    for state in typical_states:
                        if state in q_table:
                            c_value = q_table[state]['C']
                            d_value = q_table[state]['D']
                            best_action = 'C' if c_value > d_value else 'D'
                            writer.writerow([state, f"{c_value:.2f}", f"{d_value:.2f}", best_action])
                
                except Exception as e:
                    writer.writerow(['无法加载Q表数据', str(e)])
    
    except (Strategy.DoesNotExist, TournamentParticipant.DoesNotExist):
        pass  # 没有Q-learning策略，跳过
    
    return response

@login_required
def debug_q_learning_tournament(request, tournament_id):
    """
    调试视图，用于检查锦标赛的参赛者信息，特别是Q-learning策略的preset_id
    
    参数:
        request: HTTP请求对象
        tournament_id: 锦标赛ID
    """
    try:
        tournament = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        return HttpResponse("锦标赛不存在", status=404)
    
    # 获取所有参赛者及其策略信息
    participants = TournamentParticipant.objects.filter(tournament=tournament)
    
    # 构建HTML响应
    response = "<html><head><title>锦标赛参赛者调试信息</title></head><body>"
    response += f"<h1>锦标赛: {tournament.name}</h1>"
    response += "<h2>参赛者信息:</h2>"
    
    response += "<table border='1'>"
    response += "<tr><th>ID</th><th>策略名称</th><th>Preset ID</th><th>是预设策略?</th><th>总分</th><th>平均分</th><th>排名</th></tr>"
    
    # 检查是否有Q-learning策略
    has_q_learning = False
    q_learning_preset_id = None
    
    for p in participants:
        is_q_learning = False
        if p.strategy.preset_id == 'q_learning':
            has_q_learning = True
            q_learning_preset_id = p.strategy.preset_id
            is_q_learning = True
        
        response += f"<tr style='{'background-color:#e6ffe6' if is_q_learning else ''}'>"
        response += f"<td>{p.id}</td>"
        response += f"<td>{p.strategy.name}</td>"
        response += f"<td>{p.strategy.preset_id or '无'}</td>"
        response += f"<td>{'是' if p.strategy.is_preset else '否'}</td>"
        response += f"<td>{p.total_score}</td>"
        response += f"<td>{p.average_score}</td>"
        response += f"<td>{p.rank}</td>"
        response += "</tr>"
    
    response += "</table>"
    
    # 添加Q-learning状态信息
    response += "<h2>Q-learning策略状态:</h2>"
    if has_q_learning:
        response += f"<p style='color:green'>✓ 锦标赛中存在Q-learning策略，preset_id 为 '{q_learning_preset_id}'</p>"
        response += "<p>在锦标赛结果页面应该能看到 'Q-Learning分析' 按钮</p>"
    else:
        response += "<p style='color:red'>✗ 锦标赛中不存在Q-learning策略</p>"
        response += "<p>请确保添加了preset_id为'q_learning'的策略参赛者</p>"
    
    # 添加调试指南
    response += "<h2>调试步骤:</h2>"
    response += "<ol>"
    response += "<li>确保有一个策略的preset_id为'q_learning'</li>"
    response += "<li>检查模板中的条件判断 <code>{% if participant.strategy.preset_id == 'q_learning' %}</code> 是否正确</li>"
    response += "<li>尝试运行 <code>python fix_q_learning_strategy.py</code> 修复策略preset_id</li>"
    response += "</ol>"
    
    # 添加Q-learning相关视图链接
    response += "<h2>Q-learning相关视图:</h2>"
    response += f"<p><a href='/tournaments/{tournament_id}/results/'>返回锦标赛结果</a></p>"
    response += f"<p><a href='/tournaments/{tournament_id}/q_learning/'>Q-learning分析页面</a></p>"
    response += f"<p><a href='/tournaments/{tournament_id}/q_learning/curve/'>Q-learning学习曲线</a></p>"
    response += f"<p><a href='/tournaments/{tournament_id}/q_learning/heatmap/'>Q-learning Q值热力图</a></p>"
    response += f"<p><a href='/tournaments/{tournament_id}/q_learning/vs_opponents/'>Q-learning对阵结果</a></p>"
    
    response += "</body></html>"
    
    return HttpResponse(response)
