from datetime import datetime
from typing import Tuple, Dict, List
from .models import Game, Round, Strategy

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
    def execute_strategy(strategy: Strategy, opponent_history: List[str]) -> str:
        """Safely execute a strategy code to get the next move."""
        try:
            # 创建一个局部环境
            local_vars = {'history': opponent_history}
            
            # 创建一个受限的全局环境，只包含安全的模块
            safe_globals = {
                'random': __import__('random'),
                'math': __import__('math'),
                'time': __import__('time')
            }
            
            # 尝试从策略名称判断是否为内置策略
            if strategy.name == 'Always_Cooperate':
                return 'C'
            elif strategy.name == 'Always_Defect':
                return 'D'
            elif strategy.name == 'Tit for tat':
                # Tit for tat策略：第一轮合作，之后模仿对手上一轮的选择
                if not opponent_history:
                    return 'C'  # 第一轮合作
                return opponent_history[-1]  # 之后模仿对手上一轮的选择
            
            # 执行自定义策略代码
            # 注意：这是一个安全风险，生产环境中应该使用沙箱执行
            if 'def make_move(' in strategy.code:
                try:
                    # 首先执行策略代码
                    exec(strategy.code, safe_globals, local_vars)
                    
                    # 然后确保make_move函数存在
                    if 'make_move' in local_vars and callable(local_vars['make_move']):
                        # 调用make_move函数
                        result = local_vars['make_move'](opponent_history)
                        if result in ['C', 'D']:
                            return result
                    else:
                        print(f"错误：策略 {strategy.name} 中没有找到可调用的make_move函数")
                except Exception as e:
                    print(f"执行策略 {strategy.name} 的make_move函数时出错: {e}")
            else:
                print(f"错误：策略 {strategy.name} 中没有找到make_move函数定义")
            
            # 执行失败时默认返回合作
            print(f"警告：策略 {strategy.name} 执行失败，默认返回合作")
            return 'C'
        except Exception as e:
            print(f"策略 {strategy.name} 执行过程中发生错误: {e}")
            # 出错时默认合作
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
            game.completed_at = datetime.now()

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