from datetime import datetime
from typing import Tuple, Dict, List, Any
from django.utils import timezone
from .models import Game, Round, Strategy, Tournament, TournamentParticipant, TournamentMatch
import random
import time
from collections import defaultdict
import math
import json
import logging
# 导入策略模块
from .strategies import execute_strategy as exec_strategy

# 设置日志记录器
logger = logging.getLogger(__name__)

class GameService:
    @staticmethod
    def calculate_round_scores(player1_choice: str, player2_choice: str) -> Tuple[int, int]:
        """Calculate scores for a single round based on players' choices."""
        score_matrix = {
            ('C', 'C'): (3, 3),    # Both cooperate
            ('C', 'D'): (0, 5),    # Player 1 cooperates, Player 2 deceives
            ('D', 'C'): (5, 0),    # Player 1 deceives, Player 2 cooperates
            ('D', 'D'): (0, 0),    # Both deceive
        }
        return score_matrix[(player1_choice, player2_choice)]

    @staticmethod
    def execute_strategy(strategy, opponent_history, tournament_id=None):
        """执行策略，获取下一步动作
        
        参数:
            strategy: Strategy对象
            opponent_history: 对手的历史选择列表
            tournament_id: 当前锦标赛ID，用于Q-learning策略
            
        返回:
            'C' 或 'D'
        """
        try:
            # 检查是否为预设策略
            if strategy.is_preset:
                # 检查是否为Q-learning策略
                if strategy.preset_id == 'q_learning':
                    # Q-learning策略需要传递tournament_id参数
                    choice = exec_strategy(strategy.preset_id, opponent_history, tournament_id=tournament_id)
                    logger.info(f"Q-learning策略 (tournament_id={tournament_id}) 选择了: {choice}")
                    return choice
                choice = exec_strategy(strategy.preset_id, opponent_history)
                logger.info(f"预设策略 {strategy.preset_id} 选择了: {choice}")
                return choice
            else:
                # 用户自定义策略
                choice = exec_strategy(strategy.id, opponent_history)
                logger.info(f"自定义策略 {strategy.id} 选择了: {choice}")
                return choice
        except Exception as e:
            logger.error(f"执行策略 {strategy.name} 时出错: {e}")
            
            # 如果策略执行失败，根据策略类型提供默认行为，而不是总是返回'C'
            if strategy.is_preset:
                if strategy.preset_id == 'always_defect':
                    return 'D'
                elif strategy.preset_id == 'random':
                    import random
                    return random.choice(['C', 'D'])
                elif strategy.preset_id == 'tit_for_tat':
                    return 'C' if not opponent_history else opponent_history[-1]
            
            # 如果无法确定默认行为，返回合作
            return 'C'

    @staticmethod
    def play_round(game: Game) -> Round:
        """Play a single round of the game."""
        if game.current_round >= game.total_rounds:
            raise ValueError("Game has already completed all rounds")

        # 获取双方历史选择
        player1_history = []  # 玩家1历史选择
        player2_history = []  # 玩家2历史选择
        
        # 获取之前的回合记录
        previous_rounds = Round.objects.filter(game=game).order_by('round_number')
        for prev_round in previous_rounds:
            player1_history.append(prev_round.player1_choice)
            player2_history.append(prev_round.player2_choice)

        # 执行策略获取选择
        player1_choice = GameService.execute_strategy(game.strategy1, player2_history)
        player2_choice = GameService.execute_strategy(game.strategy2, player1_history)

        # Calculate scores
        p1_score, p2_score = GameService.calculate_round_scores(player1_choice, player2_choice)

        # Create and save the round
        round_number = game.current_round + 1
        round = Round.objects.create(
            game=game,
            round_number=round_number,
            player1_choice=player1_choice,
            player2_choice=player2_choice,
            player1_score=p1_score,
            player2_score=p2_score
        )

        # Update game scores and round counter
        game.player1_score += p1_score
        game.player2_score += p2_score
        game.current_round = round_number

        # Check if game is complete
        if game.current_round >= game.total_rounds:
            game.status = 'COMPLETED'
            game.completed_at = timezone.now()

        game.save()
        return round

    @staticmethod
    def create_game(strategy1: Strategy, strategy2: Strategy, total_rounds: int = 200) -> Game:
        """Create a new game between two strategies."""
        return Game.objects.create(
            strategy1=strategy1,
            strategy2=strategy2,
            total_rounds=total_rounds
        )

    @staticmethod
    def play_full_game(strategy1: Strategy, strategy2: Strategy, total_rounds: int = 200) -> Game:
        """Create and play a full game between two strategies."""
        game = GameService.create_game(strategy1, strategy2, total_rounds)
        
        while game.current_round < game.total_rounds:
            GameService.play_round(game)
        
        return game

    @staticmethod
    def get_game_summary(game: Game) -> Dict:
        """Get a summary of the game results."""
        return {
            'game_id': game.id,
            'strategy1_name': game.strategy1.name,
            'strategy2_name': game.strategy2.name,
            'player1_score': game.player1_score,
            'player2_score': game.player2_score,
            'total_rounds': game.total_rounds,
            'status': game.status,
            'winner': GameService.determine_winner(game)
        }

    @staticmethod
    def determine_winner(game: Game) -> str:
        """Determine the winner of the game."""
        if game.player1_score > game.player2_score:
            return game.strategy1.name
        elif game.player2_score > game.player1_score:
            return game.strategy2.name
        else:
            return "Tie"

# 添加新的锦标赛服务类
class TournamentService:
    @staticmethod
    def create_tournament(name: str, description: str, user, rounds_per_match: int = 200, 
                          repetitions: int = 5, payoff_matrix: Dict = None,
                          use_random_rounds: bool = False, min_rounds: int = 100, max_rounds: int = 300,
                          use_probability_model: bool = False, continue_probability: float = 0.95) -> Tournament:
        """
        创建一个新的锦标赛
        
        参数:
            name: 锦标赛名称
            description: 锦标赛描述
            user: 创建锦标赛的用户
            rounds_per_match: 每场比赛的回合数 (当use_random_rounds和use_probability_model均为False时使用)
            repetitions: 重复次数
            payoff_matrix: 自定义收益矩阵
            use_random_rounds: 是否使用随机回合数
            min_rounds: 最小回合数 (当use_random_rounds为True时使用)
            max_rounds: 最大回合数 (当use_random_rounds为True时使用)
            use_probability_model: 是否使用概率模型决定比赛是否继续下一轮
            continue_probability: 继续下一轮的概率 (当use_probability_model为True时使用)
            
        返回:
            创建的锦标赛对象
        """
        tournament = Tournament.objects.create(
            name=name,
            description=description,
            created_by=user,
            rounds_per_match=rounds_per_match,
            repetitions=repetitions,
            use_random_rounds=use_random_rounds,
            min_rounds=min_rounds,
            max_rounds=max_rounds,
            use_probability_model=use_probability_model,
            continue_probability=continue_probability
        )
        
        # 如果提供了自定义收益矩阵，则更新
        if payoff_matrix:
            tournament.payoff_matrix = payoff_matrix
            tournament.save()
            
        return tournament
    
    @staticmethod
    def add_participant(tournament: Tournament, strategy: Strategy) -> TournamentParticipant:
        """
        添加参赛者到锦标赛
        
        参数:
            tournament: 锦标赛对象
            strategy: 策略对象
            
        返回:
            创建的参赛者对象
        """
        # 检查锦标赛状态
        if tournament.status != 'CREATED':
            raise ValueError("Cannot add participants to a tournament that has already started or completed")
        
        # 检查是否已添加该策略
        if TournamentParticipant.objects.filter(tournament=tournament, strategy=strategy).exists():
            raise ValueError(f"Strategy '{strategy.name}' is already a participant in this tournament")
        
        # 创建参赛者
        return TournamentParticipant.objects.create(
            tournament=tournament,
            strategy=strategy
        )
    
    @staticmethod
    def generate_matches(tournament: Tournament) -> List[TournamentMatch]:
        """
        生成锦标赛的所有比赛
        
        参数:
            tournament: 锦标赛对象
            
        返回:
            生成的比赛列表
        """
        # 检查锦标赛状态
        if tournament.status != 'CREATED':
            raise ValueError("Matches can only be generated for tournaments in 'CREATED' status")
        
        # 获取所有参赛者
        participants = list(TournamentParticipant.objects.filter(tournament=tournament))
        
        if len(participants) < 2:
            raise ValueError("Tournament needs at least 2 participants to generate matches")
        
        created_matches = []
        
        # 对于每次重复
        for rep in range(1, tournament.repetitions + 1):
            # 生成所有可能的对阵（包括自己对自己）
            for p1 in participants:
                for p2 in participants:
                    # 创建比赛
                    match = TournamentMatch.objects.create(
                        tournament=tournament,
                        participant1=p1,
                        participant2=p2,
                        repetition=rep,
                        status='PENDING'
                    )
                    created_matches.append(match)
        
        # 更新锦标赛状态为进行中
        tournament.status = 'IN_PROGRESS'
        tournament.save()
        
        return created_matches
    
    @staticmethod
    def play_match(match: TournamentMatch) -> Dict[str, Any]:
        """
        执行一场锦标赛比赛
        
        参数:
            match: 锦标赛比赛对象
            
        返回:
            比赛结果字典
        """
        if match.status == 'COMPLETED':
            raise ValueError("Match has already been completed")
        
        tournament = match.tournament
        strategy1 = match.participant1.strategy
        strategy2 = match.participant2.strategy
        
        # 获取自定义收益矩阵
        payoff_matrix = tournament.payoff_matrix
        
        # 定义根据自定义收益矩阵计算分数的函数
        def calculate_scores(p1_choice: str, p2_choice: str) -> Tuple[float, float]:
            key = p1_choice + p2_choice
            mapped_key = {
                'CC': 'CC',
                'CD': 'CD',
                'DC': 'DC',
                'DD': 'DD'
            }.get(key)
            
            return tuple(payoff_matrix[mapped_key])
        
        # 初始化历史记录和分数
        p1_history = []  # 玩家1历史选择
        p2_history = []  # 玩家2历史选择
        p1_score = 0
        p2_score = 0
        
        # 存储每轮的选择和分数
        rounds_data = []
        
        # 根据设置确定回合数或使用概率模型
        if tournament.use_probability_model:
            # 使用概率模型，不预先确定回合数
            round_num = 1
            continue_game = True
            max_rounds = tournament.rounds_per_match  # 使用rounds_per_match作为最大回合数
            
            # 进行比赛，每轮后以概率w决定是否继续
            while continue_game and round_num <= max_rounds:  # 添加最大回合数限制
                # 执行策略获取选择
                p1_choice = GameService.execute_strategy(strategy1, p2_history, tournament_id=tournament.id)
                p2_choice = GameService.execute_strategy(strategy2, p1_history, tournament_id=tournament.id)
                
                # 计算分数
                round_p1_score, round_p2_score = calculate_scores(p1_choice, p2_choice)
                
                # 更新历史和总分
                p1_history.append(p1_choice)
                p2_history.append(p2_choice)
                p1_score += round_p1_score
                p2_score += round_p2_score
                
                # 记录回合数据
                rounds_data.append({
                    'round': round_num,
                    'p1_choice': p1_choice,
                    'p2_choice': p2_choice,
                    'p1_score': round_p1_score,
                    'p2_score': round_p2_score
                })
                
                # 确定是否继续下一轮 - 使用概率w
                continue_game = random.random() < tournament.continue_probability
                round_num += 1
        else:
            # 如果使用随机回合数，则在指定范围内随机生成回合数
            rounds_to_play = random.randint(tournament.min_rounds, tournament.max_rounds) if tournament.use_random_rounds else tournament.rounds_per_match
            
            # 进行指定回合数的对局
            for round_num in range(1, rounds_to_play + 1):
                # 执行策略获取选择
                p1_choice = GameService.execute_strategy(strategy1, p2_history, tournament_id=tournament.id)
                p2_choice = GameService.execute_strategy(strategy2, p1_history, tournament_id=tournament.id)
                
                # 计算分数
                round_p1_score, round_p2_score = calculate_scores(p1_choice, p2_choice)
                
                # 更新历史和总分
                p1_history.append(p1_choice)
                p2_history.append(p2_choice)
                p1_score += round_p1_score
                p2_score += round_p2_score
                
                # 记录回合数据
                rounds_data.append({
                    'round': round_num,
                    'p1_choice': p1_choice,
                    'p2_choice': p2_choice,
                    'p1_score': round_p1_score,
                    'p2_score': round_p2_score
                })
        
        # 更新比赛结果
        match.player1_score = p1_score
        match.player2_score = p2_score
        match.status = 'COMPLETED'
        match.completed_at = timezone.now()
        match.actual_rounds = len(rounds_data)  # 保存实际回合数
        match.save()
        
        # 返回比赛结果
        return {
            'match_id': match.id,
            'player1': strategy1.name,
            'player2': strategy2.name,
            'player1_score': p1_score,
            'player2_score': p2_score,
            'rounds': rounds_data
        }
    
    @staticmethod
    def run_tournament(tournament: Tournament, update_interval: int = None) -> Dict[str, Any]:
        """
        运行完整的锦标赛，执行所有比赛并计算结果
        
        参数:
            tournament: 锦标赛对象
            update_interval: 每执行多少场比赛更新一次进度，None表示不更新
            
        返回:
            锦标赛结果字典
        """
        # 检查锦标赛状态
        if tournament.status == 'COMPLETED':
            raise ValueError("Tournament has already been completed")
        
        if tournament.status == 'CREATED':
            # 如果是新创建的锦标赛，先生成比赛
            TournamentService.generate_matches(tournament)
        
        # 获取所有未完成的比赛
        pending_matches = TournamentMatch.objects.filter(
            tournament=tournament,
            status='PENDING'
        ).order_by('repetition')
        
        total_matches = pending_matches.count()
        completed_count = 0
        
        # 执行每场比赛
        for match in pending_matches:
            TournamentService.play_match(match)
            
            completed_count += 1
            
            # 如果设置了更新间隔，则定期更新进度
            if update_interval and completed_count % update_interval == 0:
                progress = (completed_count / total_matches) * 100
                print(f"Tournament progress: {progress:.1f}% ({completed_count}/{total_matches})")
        
        # 计算参赛者的总分和平均分
        TournamentService.calculate_results(tournament)
        
        # 更新锦标赛状态为已完成
        tournament.status = 'COMPLETED'
        tournament.completed_at = timezone.now()
        tournament.save()
        
        # 返回锦标赛结果
        return TournamentService.get_tournament_results(tournament)
    
    @staticmethod
    def calculate_results(tournament: Tournament) -> None:
        """
        计算锦标赛结果，更新每个参赛者的得分和排名
        
        参数:
            tournament: 锦标赛对象
        """
        # 获取所有参赛者
        participants = TournamentParticipant.objects.filter(tournament=tournament)
        
        # 计算每个参赛者的得分
        for participant in participants:
            # 作为玩家1的比赛
            matches_as_p1 = TournamentMatch.objects.filter(
                tournament=tournament,
                participant1=participant,
                status='COMPLETED'
            )
            
            # 作为玩家2的比赛
            matches_as_p2 = TournamentMatch.objects.filter(
                tournament=tournament,
                participant2=participant,
                status='COMPLETED'
            )
            
            # 计算总分和比赛数
            total_score = sum(m.player1_score for m in matches_as_p1) + sum(m.player2_score for m in matches_as_p2)
            total_matches = matches_as_p1.count() + matches_as_p2.count()
            
            # 计算胜负平
            wins = 0
            losses = 0
            draws = 0
            
            # 计算作为玩家1的胜负平
            for match in matches_as_p1:
                if match.player1_score > match.player2_score:
                    wins += 1
                elif match.player1_score < match.player2_score:
                    losses += 1
                else:
                    draws += 1
            
            # 计算作为玩家2的胜负平
            for match in matches_as_p2:
                if match.player2_score > match.player1_score:
                    wins += 1
                elif match.player2_score < match.player1_score:
                    losses += 1
                else:
                    draws += 1
            
            # 计算平均分
            average_score = total_score / total_matches if total_matches > 0 else 0
            
            # 更新参赛者的分数和胜负平
            participant.total_score = total_score
            participant.average_score = average_score
            
            # 保存胜负平数据
            participant.wins = wins
            participant.draws = draws
            participant.losses = losses
            
            participant.save()
        
        # 根据平均分对参赛者排名
        ranked_participants = list(participants.order_by('-average_score'))
        
        # 更新排名
        for rank, participant in enumerate(ranked_participants, 1):
            participant.rank = rank
            participant.save()
    
    @staticmethod
    def get_tournament_results(tournament: Tournament) -> Dict[str, Any]:
        """
        获取锦标赛的详细结果
        
        参数:
            tournament: 锦标赛对象
            
        返回:
            包含锦标赛详细结果的字典
        """
        # 获取所有参赛者（按排名排序）
        participants = TournamentParticipant.objects.filter(
            tournament=tournament
        ).order_by('rank')
        
        # 构建参赛者结果列表
        participant_results = []
        for p in participants:
            result = {
                'rank': p.rank,
                'strategy_name': p.strategy.name,
                'strategy_id': p.strategy.id,
                'total_score': p.total_score,
                'average_score': p.average_score
            }
            
            # 添加胜负平数据（如果存在）
            try:
                result['wins'] = p.wins
                result['draws'] = p.draws
                result['losses'] = p.losses
            except Exception:
                result['wins'] = 0
                result['draws'] = 0
                result['losses'] = 0
                
            participant_results.append(result)
        
        # 构建详细的对阵矩阵
        all_participants = list(participants)
        matchups_matrix = {}
        
        for p1 in all_participants:
            matchups_matrix[p1.strategy.name] = {}
            for p2 in all_participants:
                # 获取p1和p2之间的所有比赛
                matches = TournamentMatch.objects.filter(
                    tournament=tournament,
                    participant1=p1,
                    participant2=p2,
                    status='COMPLETED'
                )
                
                if matches.exists():
                    # 计算总分和胜负平
                    total_score = sum(m.player1_score for m in matches)
                    avg_score = total_score / matches.count()
                    wins = sum(1 for m in matches if m.player1_score > m.player2_score)
                    draws = sum(1 for m in matches if m.player1_score == m.player2_score)
                    losses = sum(1 for m in matches if m.player1_score < m.player2_score)
                    
                    # 保存更详细的对战数据
                    matchups_matrix[p1.strategy.name][p2.strategy.name] = {
                        'avg_score': avg_score,
                        'wins': wins,
                        'draws': draws,
                        'losses': losses,
                        'total': matches.count()
                    }
                else:
                    matchups_matrix[p1.strategy.name][p2.strategy.name] = 'N/A'
        
        # 构建最终结果字典
        results = {
            'tournament_id': tournament.id,
            'name': tournament.name,
            'status': tournament.status,
            'rounds_per_match': tournament.rounds_per_match,
            'repetitions': tournament.repetitions,
            'use_random_rounds': tournament.use_random_rounds,
            'min_rounds': tournament.min_rounds,
            'max_rounds': tournament.max_rounds,
            'use_probability_model': tournament.use_probability_model,
            'continue_probability': tournament.continue_probability,
            'created_by': tournament.created_by.username,
            'created_at': tournament.created_at.isoformat(),
            'completed_at': tournament.completed_at.isoformat() if tournament.completed_at else None,
            'participants': participant_results,
            'matchups_matrix': matchups_matrix,
            'payoff_matrix': tournament.payoff_matrix
        }
        
        # 添加比赛的详细信息（最多10场比赛）
        sample_matches = TournamentMatch.objects.filter(
            tournament=tournament,
            status='COMPLETED'
        ).order_by('?')[:10]
        
        match_results = []
        for match in sample_matches:
            # 从数据库获取比赛详情
            match_data = {
                'id': match.id,
                'strategy1_id': match.participant1.strategy.id,
                'strategy2_id': match.participant2.strategy.id,
                'player1_score': match.player1_score,
                'player2_score': match.player2_score,
                'score1': match.player1_score,  # 为了兼容前端的变量名
                'score2': match.player2_score,  # 为了兼容前端的变量名
                'repetition': match.repetition,
                'actual_rounds': match.actual_rounds,  # 添加实际回合数
            }
            
            # 生成回合数据（示例）- 实际上这应该从数据库中获取
            # 但由于我们不存储具体回合，这里创建一个模拟的回合列表
            rounds_data = []
            
            # 使用实际记录的回合数
            rounds_count = match.actual_rounds
            
            # 如果没有记录回合数（旧数据），则根据锦标赛设置生成一个估算值
            if rounds_count == 0:
                if tournament.use_probability_model:
                    # 使用几何分布的均值公式，μ = 1/p，其中p是停止概率
                    stop_probability = 1 - tournament.continue_probability
                    rounds_count = int(1 / stop_probability)
                elif tournament.use_random_rounds:
                    # 如果是随机回合数，使用最小和最大回合范围的中间值
                    rounds_count = (tournament.min_rounds + tournament.max_rounds) // 2
                else:
                    # 如果是固定回合数，直接使用设定的回合数
                    rounds_count = tournament.rounds_per_match
                
            # 生成模拟的回合数据
            for i in range(rounds_count):
                rounds_data.append({
                    'moves': ['C', 'C'],  # 示例移动
                    'scores': [3, 3]      # 示例分数
                })
            
            match_data['rounds'] = rounds_data
            match_results.append(match_data)
        
        results['match_results'] = match_results
        
        return results 