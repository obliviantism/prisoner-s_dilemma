from django.db import models
from django.contrib.auth.models import User

class Strategy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    code = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Game(models.Model):
    GAME_STATUS = (
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    )
    
    strategy1 = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='games_as_player1')
    strategy2 = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='games_as_player2')
    current_round = models.IntegerField(default=0)
    total_rounds = models.IntegerField(default=200)
    player1_score = models.IntegerField(default=0)
    player2_score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=GAME_STATUS, default='IN_PROGRESS')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Game {self.id}: {self.strategy1.name} vs {self.strategy2.name}"

class Round(models.Model):
    CHOICES = (
        ('C', 'Cooperate'),
        ('D', 'Defect'),
    )
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='rounds')
    round_number = models.IntegerField()
    player1_choice = models.CharField(max_length=1, choices=CHOICES)
    player2_choice = models.CharField(max_length=1, choices=CHOICES)
    player1_score = models.IntegerField()
    player2_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['game', 'round_number']
        ordering = ['round_number']

    def __str__(self):
        return f"Game {self.game.id} - Round {self.round_number}"
