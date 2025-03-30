from django.contrib import admin
from .models import Strategy, Game, Round

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
