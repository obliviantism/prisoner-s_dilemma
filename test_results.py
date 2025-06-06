import os
import django
import sys
import json
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

# 导入必要的模块
from dilemma_game.models import Strategy, Tournament, TournamentParticipant, TournamentMatch
from dilemma_game.services import TournamentService, GameService
from django.contrib.auth.models import User

def print_separator(message):
    """打印分隔符"""
    print("\n" + "="*50)
    print(f" {message} ")
    print("="*50 + "\n")

def get_tournament_results():
    """获取最近一个锦标赛的结果"""
    print_separator("获取最近一个锦标赛的结果")
    
    # 获取最近一个锦标赛
    tournament = Tournament.objects.order_by('-id').first()
    if not tournament:
        print("没有找到任何锦标赛")
        return
    
    print(f"找到锦标赛: {tournament.name} (ID: {tournament.id})")
    
    try:
        results = TournamentService.get_tournament_results(tournament)
        
        # 打印锦标赛基本信息
        print(f"锦标赛名称: {results['name']}")
        print(f"状态: {results['status']}")
        print(f"每场比赛回合数: {results['rounds_per_match']}")
        print(f"重复次数: {results['repetitions']}")
        print(f"创建者: {results['created_by']}")
        print(f"创建时间: {results['created_at']}")
        print(f"完成时间: {results['completed_at']}")
        
        # 打印参与者排名
        print("\n参与者排名:")
        for i, participant in enumerate(results['participants']):
            print(f"{i+1}. {participant['strategy_name']}: {participant['average_score']:.2f} 分 (胜: {participant['wins']}, 平: {participant['draws']}, 负: {participant['losses']})")
        
        # 打印部分对战矩阵
        print("\n对战矩阵示例 (前3个策略):")
        strategies = list(results['matchups_matrix'].keys())[:3]
        for s1 in strategies:
            for s2 in strategies:
                matchup = results['matchups_matrix'][s1][s2]
                if isinstance(matchup, dict):
                    print(f"{s1} vs {s2}: 平均分 {matchup['avg_score']:.2f}, 胜/平/负: {matchup['wins']}/{matchup['draws']}/{matchup['losses']}")
                else:
                    print(f"{s1} vs {s2}: {matchup}")
        
    except Exception as e:
        print(f"获取锦标赛结果时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_tournament_results() 