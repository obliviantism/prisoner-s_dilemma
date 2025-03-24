from enum import Enum
import random

class Choice(Enum):
    COOPERATE = 'C'
    DEFECT = 'D'

class Strategy:
    def __init__(self, name):
        self.name = name
        self.history = []
        self.score = 0
        
    def make_choice(self, opponent_history):
        raise NotImplementedError("Subclasses must implement make_choice()")
    
    def add_result(self, my_choice, opponent_choice, points):
        self.history.append((my_choice, opponent_choice))
        self.score += points

class AlwaysCooperate(Strategy):
    def make_choice(self, opponent_history):
        return Choice.COOPERATE

class AlwaysDefect(Strategy):
    def make_choice(self, opponent_history):
        return Choice.DEFECT

class TitForTat(Strategy):
    def make_choice(self, opponent_history):
        if not opponent_history:
            return Choice.COOPERATE
        return opponent_history[-1]

class RandomStrategy(Strategy):
    def make_choice(self, opponent_history):
        return random.choice([Choice.COOPERATE, Choice.DEFECT])



class PrisonersDilemma:
    def __init__(self, rounds=200):
        self.rounds = rounds
        self.payoff_matrix = {
            (Choice.COOPERATE, Choice.COOPERATE): (3, 3),
            (Choice.COOPERATE, Choice.DEFECT): (0, 5),
            (Choice.DEFECT, Choice.COOPERATE): (5, 0),
            (Choice.DEFECT, Choice.DEFECT): (0, 0)
        }

    def play_game(self, player1, player2):
        for _ in range(self.rounds):
            # Get choices from both players
            p1_choice = player1.make_choice([h[1] for h in player1.history])
            p2_choice = player2.make_choice([h[1] for h in player2.history])
            
            # Calculate scores
            p1_points, p2_points = self.payoff_matrix[(p1_choice, p2_choice)]
            
            # Update player histories and scores
            player1.add_result(p1_choice, p2_choice, p1_points)
            player2.add_result(p2_choice, p1_choice, p2_points)

        return player1.score, player2.score

def main():
    # Create strategies
    strategies = [
        AlwaysCooperate("Always Cooperate"),
        AlwaysDefect("Always Defect"),
        TitForTat("Tit for Tat"),
        RandomStrategy("Random")
    ]
    
    game = PrisonersDilemma(rounds=200)
    
    # Play each strategy against each other
    for i in range(len(strategies)):
        for j in range(i + 1, len(strategies)):
            player1 = strategies[i]
            player2 = strategies[j]
            
            # Reset scores and histories
            player1.score = 0
            player2.score = 0
            player1.history = []
            player2.history = []
            
            score1, score2 = game.play_game(player1, player2)
            print(f"{player1.name} vs {player2.name}")
            print(f"Scores: {score1} - {score2}")
            print("-" * 30)

if __name__ == "__main__":
    main() 