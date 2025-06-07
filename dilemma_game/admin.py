from django.contrib import admin
from .models import Strategy, Game, Round, Tournament, TournamentParticipant, TournamentMatch

# Register your models here.

@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'code')
    list_filter = ('created_by', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'strategy1', 'strategy2', 'current_round', 'total_rounds', 
                  'player1_score', 'player2_score', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('strategy1__name', 'strategy2__name')
    readonly_fields = ('created_at', 'completed_at')

@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ('game', 'round_number', 'player1_choice', 'player2_choice', 
                   'player1_score', 'player2_score', 'created_at')
    list_filter = ('player1_choice', 'player2_choice', 'created_at')
    search_fields = ('game__id',)
    readonly_fields = ('created_at',)

# 注册锦标赛相关模型
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'rounds_per_match', 'repetitions', 'created_by', 'created_at')
    list_filter = ('status', 'created_by', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'completed_at')

@admin.register(TournamentParticipant)
class TournamentParticipantAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'strategy', 'total_score', 'average_score', 'rank', 
                   'wins', 'draws', 'losses')
    list_filter = ('tournament', 'strategy')
    search_fields = ('tournament__name', 'strategy__name')

@admin.register(TournamentMatch)
class TournamentMatchAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'participant1', 'participant2', 'repetition', 
                   'player1_score', 'player2_score', 'status', 'created_at')
    list_filter = ('tournament', 'status', 'created_at')
    search_fields = ('tournament__name', 'participant1__strategy__name', 'participant2__strategy__name')
    readonly_fields = ('created_at', 'completed_at')
