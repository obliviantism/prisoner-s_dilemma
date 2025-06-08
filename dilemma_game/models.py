from django.db import models
from django.contrib.auth.models import User
import json

class Strategy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    code = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # 新增字段，标识是否为预设策略
    is_preset = models.BooleanField(default=False)
    # 预设策略的ID，用于再次添加
    preset_id = models.CharField(max_length=50, blank=True, null=True)

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
        ('D', 'Deceive'),
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

# 锦标赛模式的新模型
class Tournament(models.Model):
    TOURNAMENT_STATUS = (
        ('CREATED', 'Created'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    rounds_per_match = models.IntegerField(default=200)
    # 新增字段，用于控制是否使用随机回合数
    use_random_rounds = models.BooleanField(default=False)
    min_rounds = models.IntegerField(default=100)  # 最小回合数
    max_rounds = models.IntegerField(default=300)  # 最大回合数
    # 新增字段，用于控制是否使用概率模型决定是否继续下一轮
    use_probability_model = models.BooleanField(default=False)
    # 新增字段，下一轮的继续概率 (0-1之间)
    continue_probability = models.FloatField(default=0.95)
    repetitions = models.IntegerField(default=5)  # 每场锦标赛重复次数
    status = models.CharField(max_length=20, choices=TOURNAMENT_STATUS, default='CREATED')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # 存储自定义的收益矩阵
    payoff_matrix_json = models.TextField(default='{"CC":[3,3],"CD":[0,5],"DC":[5,0],"DD":[0,0]}')
    
    @property
    def payoff_matrix(self):
        """返回收益矩阵字典"""
        return json.loads(self.payoff_matrix_json)
    
    @payoff_matrix.setter
    def payoff_matrix(self, matrix_dict):
        """设置收益矩阵"""
        self.payoff_matrix_json = json.dumps(matrix_dict)
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

class TournamentParticipant(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='participants')
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    total_score = models.FloatField(default=0)  # 锦标赛中的总分
    average_score = models.FloatField(default=0)  # 平均每场得分
    rank = models.IntegerField(null=True, blank=True)  # 排名
    # 添加胜负平统计
    wins = models.IntegerField(default=0)  # 胜场数
    draws = models.IntegerField(default=0)  # 平局数
    losses = models.IntegerField(default=0)  # 负场数
    
    class Meta:
        unique_together = ['tournament', 'strategy']
    
    def __str__(self):
        return f"{self.strategy.name} in {self.tournament.name}"

class TournamentMatch(models.Model):
    MATCH_STATUS = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
    )
    
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    participant1 = models.ForeignKey(TournamentParticipant, on_delete=models.CASCADE, related_name='matches_as_player1')
    participant2 = models.ForeignKey(TournamentParticipant, on_delete=models.CASCADE, related_name='matches_as_player2')
    repetition = models.IntegerField()  # 第几次重复
    player1_score = models.FloatField(default=0)
    player2_score = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=MATCH_STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    actual_rounds = models.IntegerField(default=0)  # 实际进行的回合数
    
    class Meta:
        unique_together = ['tournament', 'participant1', 'participant2', 'repetition']
    
    def __str__(self):
        return f"{self.participant1.strategy.name} vs {self.participant2.strategy.name} (Rep {self.repetition})"
