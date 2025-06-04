from rest_framework import serializers
from .models import Strategy, Game, Round, Tournament, TournamentParticipant, TournamentMatch

class StrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = Strategy
        fields = ['id', 'name', 'description', 'code', 'created_by', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class RoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        fields = ['id', 'game', 'round_number', 'player1_choice', 'player2_choice', 
                 'player1_score', 'player2_score', 'created_at']
        read_only_fields = ['created_at']

class GameSerializer(serializers.ModelSerializer):
    rounds = RoundSerializer(many=True, read_only=True)
    strategy1 = StrategySerializer(read_only=True)
    strategy2 = StrategySerializer(read_only=True)
    
    class Meta:
        model = Game
        fields = ['id', 'strategy1', 'strategy2', 'current_round', 'total_rounds',
                 'player1_score', 'player2_score', 'status', 'created_at',
                 'completed_at', 'rounds']
        read_only_fields = ['current_round', 'player1_score', 'player2_score',
                           'status', 'created_at', 'completed_at']

# 添加锦标赛相关的序列化器
class TournamentParticipantSerializer(serializers.ModelSerializer):
    strategy = StrategySerializer(read_only=True)
    
    class Meta:
        model = TournamentParticipant
        fields = ['id', 'strategy', 'total_score', 'average_score', 'rank']
        read_only_fields = ['total_score', 'average_score', 'rank']

class TournamentMatchSerializer(serializers.ModelSerializer):
    participant1 = TournamentParticipantSerializer(read_only=True)
    participant2 = TournamentParticipantSerializer(read_only=True)
    
    class Meta:
        model = TournamentMatch
        fields = ['id', 'tournament', 'participant1', 'participant2', 'repetition',
                  'player1_score', 'player2_score', 'status', 'created_at', 'completed_at']
        read_only_fields = ['player1_score', 'player2_score', 'status', 'created_at', 'completed_at']

class TournamentSerializer(serializers.ModelSerializer):
    participants = TournamentParticipantSerializer(many=True, read_only=True)
    matches = serializers.SerializerMethodField()
    payoff_matrix = serializers.JSONField(read_only=True)
    created_by_username = serializers.SerializerMethodField()
    
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'description', 'created_by', 'created_by_username',
                  'rounds_per_match', 'repetitions', 'status', 'created_at',
                  'completed_at', 'payoff_matrix', 'participants', 'matches']
        read_only_fields = ['created_by', 'status', 'created_at', 'completed_at']
    
    def get_matches(self, obj):
        # 只返回前10个比赛，避免返回过多数据
        matches = TournamentMatch.objects.filter(tournament=obj)[:10]
        return TournamentMatchSerializer(matches, many=True).data
    
    def get_created_by_username(self, obj):
        return obj.created_by.username 