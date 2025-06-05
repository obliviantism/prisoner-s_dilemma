#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
重新创建锦标赛的辅助脚本

使用方法:
python recreate_tournament.py <source_tournament_id>

例如:
python recreate_tournament.py 29
"""

import os
import sys
import django
import json
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from dilemma_game.models import Tournament, TournamentParticipant, Strategy
from dilemma_game.services import TournamentService

def recreate_tournament(source_tournament_id):
    """
    基于现有锦标赛创建一个新的锦标赛，但使用正确的收益矩阵
    
    参数:
        source_tournament_id: 源锦标赛ID
    """
    try:
        # 获取源锦标赛对象
        source_tournament = Tournament.objects.get(id=source_tournament_id)
        
        # 打印源锦标赛信息
        print(f"源锦标赛(ID={source_tournament_id})信息:")
        print(f"名称: {source_tournament.name}")
        print(f"描述: {source_tournament.description}")
        print(f"每场比赛回合数: {source_tournament.rounds_per_match}")
        print(f"重复次数: {source_tournament.repetitions}")
        
        # 打印当前的收益矩阵
        current_matrix = source_tournament.payoff_matrix
        print(f"\n当前收益矩阵:")
        print(json.dumps(current_matrix, indent=2, ensure_ascii=False))
        
        # 创建一个新的收益矩阵，确保DD单元格的值为[0, 0]
        new_matrix = current_matrix.copy()
        new_matrix['DD'] = [0, 0]
        
        print(f"\n新的收益矩阵:")
        print(json.dumps(new_matrix, indent=2, ensure_ascii=False))
        
        # 创建新的锦标赛名称
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{source_tournament.name}_修复_{timestamp}"
        
        # 询问用户是否要创建新的锦标赛
        while True:
            choice = input(f"\n是否要创建新的锦标赛 '{new_name}'? (y/n): ").strip().lower()
            if choice in ['y', 'n']:
                break
            print("请输入y或n")
        
        if choice == 'y':
            # 创建新的锦标赛
            new_tournament = TournamentService.create_tournament(
                name=new_name,
                description=f"基于锦标赛ID={source_tournament_id}创建，修复了收益矩阵。原描述: {source_tournament.description}",
                user=source_tournament.created_by,
                rounds_per_match=source_tournament.rounds_per_match,
                repetitions=source_tournament.repetitions,
                payoff_matrix=new_matrix,
                use_random_rounds=source_tournament.use_random_rounds,
                min_rounds=source_tournament.min_rounds,
                max_rounds=source_tournament.max_rounds
            )
            
            print(f"\n成功创建新的锦标赛(ID={new_tournament.id})")
            
            # 获取源锦标赛的参赛者
            source_participants = TournamentParticipant.objects.filter(tournament=source_tournament)
            print(f"\n源锦标赛有{source_participants.count()}个参赛者")
            
            # 添加参赛者到新的锦标赛
            for participant in source_participants:
                try:
                    TournamentService.add_participant(new_tournament, participant.strategy)
                    print(f"已添加策略 '{participant.strategy.name}' 到新的锦标赛")
                except Exception as e:
                    print(f"添加策略 '{participant.strategy.name}' 时出错: {str(e)}")
            
            # 询问用户是否要立即运行新的锦标赛
            while True:
                run_choice = input("\n是否要立即运行新的锦标赛? (y/n): ").strip().lower()
                if run_choice in ['y', 'n']:
                    break
                print("请输入y或n")
            
            if run_choice == 'y':
                # 运行新的锦标赛
                print("\n正在运行新的锦标赛...")
                try:
                    results = TournamentService.run_tournament(new_tournament)
                    print("锦标赛已成功运行完成")
                    
                    # 打印部分结果
                    print("\n锦标赛结果摘要:")
                    for p in results['participants']:
                        print(f"{p['strategy_name']}: 总分={p['total_score']}, 平均分={p['average_score']:.2f}, "
                              f"胜={p.get('wins', 0)}, 平={p.get('draws', 0)}, 负={p.get('losses', 0)}")
                    
                except Exception as e:
                    print(f"运行锦标赛时出错: {str(e)}")
            else:
                print("\n未运行新的锦标赛")
        else:
            print("\n操作已取消")
    
    except Tournament.DoesNotExist:
        print(f"找不到ID为{source_tournament_id}的锦标赛")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python recreate_tournament.py <source_tournament_id>")
        sys.exit(1)
    
    try:
        tournament_id = int(sys.argv[1])
        recreate_tournament(tournament_id)
    except ValueError:
        print("锦标赛ID必须是整数")
        sys.exit(1) 