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
    # 使用SerializerMethodField来更好地控制错误处理
    participants = serializers.SerializerMethodField()
    matches = serializers.SerializerMethodField()
    payoff_matrix = serializers.JSONField(read_only=True)
    created_by_username = serializers.SerializerMethodField()
    
    class Meta:
        model = Tournament
        fields = ['id', 'name', 'description', 'created_by', 'created_by_username',
                  'rounds_per_match', 'use_random_rounds', 'min_rounds', 'max_rounds', 
                  'repetitions', 'status', 'created_at',
                  'completed_at', 'payoff_matrix', 'participants', 'matches']
        read_only_fields = ['created_by', 'status', 'created_at', 'completed_at']
    
    def get_participants(self, obj):
        """安全地获取参赛者数据"""
        try:
            participants = TournamentParticipant.objects.filter(tournament=obj)
            result = []
            for p in participants:
                try:
                    result.append({
                        'id': p.id,
                        'strategy': {
                            'id': p.strategy.id,
                            'name': p.strategy.name,
                            'description': p.strategy.description,
                        },
                        'total_score': p.total_score,
                        'average_score': p.average_score,
                        'rank': p.rank
                    })
                except Exception as e:
                    print(f"处理参赛者错误 (ID={p.id}): {str(e)}")
            return result
        except Exception as e:
            print(f"获取锦标赛参赛者列表错误: {str(e)}")
            return []  # 发生错误时返回空列表
    
    def get_matches(self, obj):
        """安全地获取比赛数据"""
        try:
            # 只返回前10个比赛，避免返回过多数据
            matches = TournamentMatch.objects.filter(tournament=obj)[:10]
            result = []
            for m in matches:
                try:
                    result.append({
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
                        'status': m.status,
                        'created_at': m.created_at,
                        'completed_at': m.completed_at
                    })
                except Exception as e:
                    print(f"处理比赛错误 (ID={m.id}): {str(e)}")
            return result
        except Exception as e:
            print(f"获取锦标赛比赛列表错误: {str(e)}")
            return []  # 发生错误时返回空列表
    
    def get_created_by_username(self, obj):
        """安全地获取创建者用户名"""
        try:
            return obj.created_by.username if obj.created_by else ""
        except Exception as e:
            print(f"获取创建者用户名错误: {str(e)}")
            return ""  # 如果获取用户名失败，返回空字符串 