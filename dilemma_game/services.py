from datetime import datetime
from typing import Tuple, Dict
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
    def play_round(game: Game) -> Round:
        """Play a single round of the game."""
        if game.current_round >= game.total_rounds:
            raise ValueError("Game has already completed all rounds")

        # Execute strategies to get choices
        # Note: In a real implementation, we would safely execute the strategy code
        # For now, we'll use a simple example (random choice)
        import random
        player1_choice = random.choice(['C', 'D'])
        player2_choice = random.choice(['C', 'D'])

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