"""
运行一个模拟Axelrod第一次锦标赛的Django锦标赛

将所有15个Axelrod策略添加到一个锦标赛中，并运行比赛
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from django.contrib.auth.models import User
from dilemma_game.models import Strategy, Tournament, TournamentParticipant, TournamentMatch
from dilemma_game.services import TournamentService
from django.utils import timezone

def run_axelrod_tournament():
    print("创建并运行Axelrod第一次锦标赛模拟...")
    
    # 获取或创建测试用户
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        print("创建测试用户")
    
    # 创建锦标赛
    tournament = Tournament.objects.create(
        name='Axelrod第一次锦标赛模拟',
        description='模拟Robert Axelrod在1980年组织的第一次囚徒困境锦标赛，包含了原始的15个策略。',
        created_by=user,
        rounds_per_match=200,  # Axelrod锦标赛使用200轮
        repetitions=1,         # 简单起见，每对策略只进行1次比赛
        status='CREATED'
    )
    print(f"创建锦标赛: {tournament.name}")
    
    # Axelrod第一次锦标赛的策略ID列表
    axelrod_strategy_ids = [
        # 原始策略
        'tit_for_tat',         # Anatol Rapoport的策略，赢得了锦标赛
        'always_cooperate',    # 始终合作策略
        'always_defect',       # 始终背叛策略
        'random',              # 随机策略
        'grudger',             # Friedman的"永不原谅"策略
        
        # 新添加的策略
        'davis',               # Davis的策略
        'joss',                # Joss的策略 
        'tullock',             # Tullock的策略
        'nydegger',            # Nydegger的策略
        'grofman',             # Grofman的策略
        'shubik',              # Shubik的策略
        'stein_and_rapoport',  # Stein & Rapoport的策略
        'downing',             # Downing的策略
        'graaskamp',           # Graaskamp的策略
        'tideman_and_chieruzzi' # Tideman & Chieruzzi的策略
    ]
    
    # 添加策略到锦标赛
    strategy_count = 0
    for strategy_id in axelrod_strategy_ids:
        try:
            # 查找策略
            strategy = Strategy.objects.get(preset_id=strategy_id)
            
            # 添加到锦标赛
            participant = TournamentService.add_participant(tournament, strategy)
            print(f"添加策略: {strategy.name}")
            strategy_count += 1
        except Strategy.DoesNotExist:
            print(f"警告: 找不到策略 {strategy_id}")
        except Exception as e:
            print(f"添加策略 {strategy_id} 时出错: {str(e)}")
    
    print(f"成功添加了 {strategy_count} 个策略到锦标赛")
    
    # 生成锦标赛比赛
    try:
        matches = TournamentService.generate_matches(tournament)
        print(f"生成了{len(matches)}场比赛")
        
        # 运行锦标赛
        print("开始运行锦标赛，这可能需要一些时间...")
        TournamentService.run_tournament(tournament)
        print("锦标赛运行完成")
        
        # 更新锦标赛状态为已完成
        tournament.status = 'COMPLETED'
        tournament.completed_at = timezone.now()
        tournament.save()
        
        # 计算结果
        TournamentService.calculate_results(tournament)
        print("结果计算完成")
        
        # 打印结果
        participants = TournamentParticipant.objects.filter(tournament=tournament).order_by('rank')
        
        print("\n===== Axelrod锦标赛结果 =====")
        print("排名\t策略\t总分\t平均分\t胜/平/负")
        print("="*50)
        
        for p in participants:
            print(f"{p.rank}\t{p.strategy.name}\t{p.total_score:.1f}\t{p.average_score:.2f}\t{p.wins}/{p.draws}/{p.losses}")
        
        # 验证针锋相对(Tit for Tat)是否赢得了锦标赛，就像在原始Axelrod锦标赛中那样
        tft_participant = next((p for p in participants if p.strategy.preset_id == 'tit_for_tat'), None)
        if tft_participant and tft_participant.rank == 1:
            print("\n历史重演！针锋相对(Tit for Tat)策略再次赢得了锦标赛，就像在1980年的原始Axelrod锦标赛中一样!")
        
        print(f"\n测试完成！现在可以访问 http://127.0.0.1:8000/tournaments/{tournament.id}/results/ 查看结果")
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == '__main__':
    run_axelrod_tournament() 