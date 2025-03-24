from rest_framework import serializers
from .models import Strategy, Game, Round

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
    
    class Meta:
        model = Game
        fields = ['id', 'strategy1', 'strategy2', 'current_round', 'total_rounds',
                 'player1_score', 'player2_score', 'status', 'created_at',
                 'completed_at', 'rounds']
        read_only_fields = ['current_round', 'player1_score', 'player2_score',
                           'status', 'created_at', 'completed_at'] 