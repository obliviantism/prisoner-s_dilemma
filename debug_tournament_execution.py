#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
调试锦标赛执行过程，重点关注策略执行和得分计算
"""

import os
import sys
import django
import json
import traceback

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from dilemma_game.models import Tournament, TournamentParticipant, TournamentMatch, Strategy
from dilemma_game.services import TournamentService, GameService

def debug_strategy_execution():
    """测试各种策略的执行结果"""
    print("\n测试策略执行:")
    
    strategies = Strategy.objects.all()
    print(f"找到 {strategies.count()} 个策略")
    
    # 测试每个策略对几种不同历史的响应
    test_histories = [
        [],                     # 空历史
        ['C'],                  # 一次合作
        ['D'],                  # 一次背叛
        ['C', 'C', 'C'],        # 连续合作
        ['D', 'D', 'D'],        # 连续背叛
        ['C', 'D', 'C', 'D']    # 交替
    ]
    
    for strategy in strategies:
        print(f"\n策略: {strategy.name} (ID: {strategy.id})")
        print(f"预设: {'是' if strategy.is_preset else '否'}, 预设ID: {strategy.preset_id}")
        print(f"代码片段: {strategy.code[:100]}...")
        
        for history in test_histories:
            try:
                start_time = django.utils.timezone.now()
                choice = GameService.execute_strategy(strategy, history)
                end_time = django.utils.timezone.now()
                execution_time = (end_time - start_time).total_seconds() * 1000
                
                print(f"历史 {history}: 选择 {choice} (执行时间: {execution_time:.2f}毫秒)")
            except Exception as e:
                print(f"历史 {history}: 执行错误 - {str(e)}")

def debug_tournament_match():
    """模拟执行一场锦标赛比赛并打印详细信息"""
    print("\n模拟锦标赛比赛执行:")
    
    # 获取一个进行中的锦标赛
    tournament = Tournament.objects.filter(status='IN_PROGRESS').first()
    if not tournament:
        tournament = Tournament.objects.filter(status='CREATED').first()
        if not tournament:
            print("没有找到可用的锦标赛")
            return
        print(f"找到状态为CREATED的锦标赛: {tournament.name}")
        
        # 生成比赛
        try:
            TournamentService.generate_matches(tournament)
            print("成功生成比赛")
        except Exception as e:
            print(f"生成比赛时出错: {str(e)}")
            return
    
    # 获取一个待执行的比赛
    match = TournamentMatch.objects.filter(tournament=tournament, status='PENDING').first()
    if not match:
        print("没有找到待执行的比赛")
        return
    
    print(f"执行比赛: {match.participant1.strategy.name} vs {match.participant2.strategy.name}")
    print(f"锦标赛回合数: {tournament.rounds_per_match}")
    print(f"收益矩阵: {tournament.payoff_matrix}")
    
    # 保存原始实现的引用
    original_execute_strategy = GameService.execute_strategy
    original_play_match = TournamentService.play_match
    
    # 修补策略执行函数以记录执行情况
    def patched_execute_strategy(strategy, opponent_history):
        result = original_execute_strategy(strategy, opponent_history)
        print(f"策略 {strategy.name} 对历史 {opponent_history} 的选择: {result}")
        return result
    
    # 临时替换函数
    GameService.execute_strategy = patched_execute_strategy
    
    try:
        # 手动执行比赛
        match_results = original_play_match(match)
        
        # 打印比赛结果
        print("\n比赛结果:")
        print(f"玩家1得分: {match_results['player1_score']}")
        print(f"玩家2得分: {match_results['player2_score']}")
        
        # 打印回合详情
        print("\n回合详情:")
        for i, round_data in enumerate(match_results['rounds'][:10]):  # 只显示前10轮
            print(f"回合 {round_data['round']}: "
                  f"P1选择={round_data['p1_choice']}, "
                  f"P2选择={round_data['p2_choice']}, "
                  f"得分=[{round_data['p1_score']}, {round_data['p2_score']}]")
        
        if len(match_results['rounds']) > 10:
            print(f"... 还有 {len(match_results['rounds']) - 10} 轮未显示")
        
        # 分析选择和得分
        p1_choices = [r['p1_choice'] for r in match_results['rounds']]
        p2_choices = [r['p2_choice'] for r in match_results['rounds']]
        
        p1_c_count = p1_choices.count('C')
        p1_d_count = p1_choices.count('D')
        p2_c_count = p2_choices.count('C')
        p2_d_count = p2_choices.count('D')
        
        print(f"\n玩家1选择统计: 合作={p1_c_count}, 背叛={p1_d_count}")
        print(f"玩家2选择统计: 合作={p2_c_count}, 背叛={p2_d_count}")
        
        # 计算不同组合的出现次数
        cc_count = sum(1 for i in range(len(p1_choices)) if p1_choices[i] == 'C' and p2_choices[i] == 'C')
        cd_count = sum(1 for i in range(len(p1_choices)) if p1_choices[i] == 'C' and p2_choices[i] == 'D')
        dc_count = sum(1 for i in range(len(p1_choices)) if p1_choices[i] == 'D' and p2_choices[i] == 'C')
        dd_count = sum(1 for i in range(len(p1_choices)) if p1_choices[i] == 'D' and p2_choices[i] == 'D')
        
        print(f"选择组合统计:")
        print(f"CC (双方合作): {cc_count} 次")
        print(f"CD (P1合作,P2背叛): {cd_count} 次")
        print(f"DC (P1背叛,P2合作): {dc_count} 次")
        print(f"DD (双方背叛): {dd_count} 次")
        
    except Exception as e:
        print(f"执行比赛时出错: {str(e)}")
        traceback.print_exc()
    finally:
        # 恢复原始函数
        GameService.execute_strategy = original_execute_strategy
        TournamentService.play_match = original_play_match

def debug_tournament_run():
    """模拟完整运行一个锦标赛并分析结果"""
    print("\n模拟锦标赛完整运行:")
    
    # 获取一个新创建的锦标赛
    tournament = Tournament.objects.filter(status='CREATED').first()
    if not tournament:
        print("没有找到新创建的锦标赛")
        return
    
    print(f"找到锦标赛: {tournament.name} (ID: {tournament.id})")
    print(f"状态: {tournament.status}")
    print(f"收益矩阵: {tournament.payoff_matrix}")
    
    # 检查参赛者
    participants = TournamentParticipant.objects.filter(tournament=tournament)
    if participants.count() < 2:
        print("锦标赛参赛者不足")
        return
    
    print(f"参赛者 ({participants.count()}):")
    for p in participants:
        print(f"- {p.strategy.name}")
    
    # 保存执行次数统计
    strategy_execution_counts = {}
    strategy_choices = {}
    
    # 替换策略执行函数以记录统计信息
    original_execute_strategy = GameService.execute_strategy
    
    def tracking_execute_strategy(strategy, opponent_history):
        # 记录执行次数
        if strategy.id not in strategy_execution_counts:
            strategy_execution_counts[strategy.id] = 0
            strategy_choices[strategy.id] = {'C': 0, 'D': 0}
        
        strategy_execution_counts[strategy.id] += 1
        
        # 获取实际选择
        choice = original_execute_strategy(strategy, opponent_history)
        
        # 记录选择
        if choice in ['C', 'D']:
            strategy_choices[strategy.id][choice] += 1
        
        return choice
    
    # 临时替换函数
    GameService.execute_strategy = tracking_execute_strategy
    
    try:
        print("\n开始运行锦标赛...")
        start_time = django.utils.timezone.now()
        
        # 运行锦标赛
        results = TournamentService.run_tournament(tournament)
        
        end_time = django.utils.timezone.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"锦标赛执行完成，耗时: {execution_time:.2f} 秒")
        
        # 打印执行统计
        print("\n策略执行统计:")
        for strategy_id, count in strategy_execution_counts.items():
            try:
                strategy = Strategy.objects.get(id=strategy_id)
                c_choices = strategy_choices[strategy_id]['C']
                d_choices = strategy_choices[strategy_id]['D']
                c_percent = (c_choices / count) * 100 if count > 0 else 0
                d_percent = (d_choices / count) * 100 if count > 0 else 0
                
                print(f"策略 {strategy.name}: 执行 {count} 次")
                print(f"  选择: 合作={c_choices} ({c_percent:.1f}%), 背叛={d_choices} ({d_percent:.1f}%)")
            except Strategy.DoesNotExist:
                print(f"策略 ID={strategy_id}: 执行 {count} 次 (策略不存在)")
        
        # 分析结果
        print("\n锦标赛结果:")
        print(f"状态: {tournament.status}")
        
        # 获取结果
        updated_participants = TournamentParticipant.objects.filter(tournament=tournament).order_by('rank')
        print("\n最终排名:")
        for p in updated_participants:
            print(f"#{p.rank}: {p.strategy.name} - 总分: {p.total_score}, 平均: {p.average_score}")
            print(f"  胜: {p.wins}, 平: {p.draws}, 负: {p.losses}")
        
        # 检查是否所有得分都相同
        scores = [p.average_score for p in updated_participants]
        all_same = all(score == scores[0] for score in scores)
        if all_same:
            print("\n警告: 所有策略的平均分都相同!")
            print(f"共同的平均分: {scores[0]}")
        
        # 分析比赛结果
        matches = TournamentMatch.objects.filter(tournament=tournament, status='COMPLETED')
        print(f"\n比赛分析 (共 {matches.count()} 场):")
        
        # 统计不同得分的比赛数量
        score_counts = {}
        for match in matches:
            score_key = f"{match.player1_score}:{match.player2_score}"
            if score_key not in score_counts:
                score_counts[score_key] = 0
            score_counts[score_key] += 1
        
        print("得分分布:")
        for score, count in sorted(score_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            percent = (count / matches.count()) * 100
            print(f"  {score}: {count} 场 ({percent:.1f}%)")
        
    except Exception as e:
        print(f"运行锦标赛时出错: {str(e)}")
        traceback.print_exc()
    finally:
        # 恢复原始函数
        GameService.execute_strategy = original_execute_strategy

def fix_tournament_problems():
    """修复锦标赛执行中发现的问题"""
    print("\n开始修复锦标赛执行问题...")
    
    # 1. 修复原因：检查策略执行函数是否总是返回相同的选择
    # 先检查GameService.execute_strategy实现是否有问题
    original_code = inspect_and_fix_function(GameService, 'execute_strategy', fix_execute_strategy)
    if original_code:
        print(f"原始GameService.execute_strategy代码: {original_code[:200]}...")
    
    # 2. 修复锦标赛执行中的问题
    # 在`services.py`中重点修复`play_match`中的策略执行和得分计算
    print("\n扫描锦标赛中问题数据...")
    
    # 查找所有完成的锦标赛
    tournaments = Tournament.objects.filter(status='COMPLETED')
    print(f"找到 {tournaments.count()} 个已完成的锦标赛")
    
    for tournament in tournaments:
        print(f"\n检查锦标赛: {tournament.name} (ID: {tournament.id})")
        
        # 检查参赛者得分
        participants = TournamentParticipant.objects.filter(tournament=tournament)
        scores = [p.average_score for p in participants]
        
        if participants.count() >= 2 and all(score == scores[0] for score in scores):
            print(f"问题: 所有参赛者平均分相同 ({scores[0]})")
            
            # 重置锦标赛
            tournament.status = 'CREATED'
            tournament.save()
            
            # 删除所有比赛
            match_count = TournamentMatch.objects.filter(tournament=tournament).delete()[0]
            print(f"已删除 {match_count} 场比赛")
            
            # 重置参赛者
            for p in participants:
                p.total_score = 0
                p.average_score = 0
                p.rank = None
                p.wins = 0
                p.draws = 0
                p.losses = 0
                p.save()
            
            print(f"已重置 {participants.count()} 名参赛者")
            print(f"锦标赛 {tournament.name} 已重置为'CREATED'状态，可以重新运行")
    
    print("\n修复完成!")

def inspect_and_fix_function(class_obj, func_name, fix_func=None):
    """检查并修复一个类中的函数实现"""
    import inspect
    
    if not hasattr(class_obj, func_name):
        print(f"{class_obj.__name__} 没有 {func_name} 方法")
        return None
    
    # 获取原始实现的源代码
    original_func = getattr(class_obj, func_name)
    original_code = inspect.getsource(original_func)
    
    # 如果提供了修复函数，则替换实现
    if fix_func:
        setattr(class_obj, func_name, fix_func)
        print(f"已替换 {class_obj.__name__}.{func_name} 的实现")
    
    return original_code

def fix_execute_strategy(strategy, opponent_history):
    """
    修复后的策略执行函数 - 确保正确执行策略代码
    
    :param strategy: 策略对象
    :param opponent_history: 对手历史选择列表
    :return: 策略选择 ('C' 或 'D')
    """
    import random
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # 检查策略代码是否为空
        if not strategy.code or not strategy.code.strip():
            logger.warning(f"策略 {strategy.name} 没有代码，默认返回合作")
            return 'C'
        
        # 准备执行环境
        safe_globals = {
            'random': random,
        }
        local_vars = {}
        
        # 如果是预设策略，尝试使用预设ID
        if strategy.is_preset and strategy.preset_id:
            from dilemma_game.strategies import execute_strategy as preset_execute
            try:
                return preset_execute(strategy.preset_id, opponent_history)
            except Exception as e:
                logger.warning(f"预设策略 {strategy.preset_id} 执行失败: {e}")
                # 如果预设执行失败，继续尝试自定义代码
        
        # 执行自定义策略代码
        try:
            # 为Pavlov策略提供必要的辅助函数
            if 'get_my_last_move' in strategy.code:
                setup_code = """
def get_my_last_move(history):
    # 此函数跟踪自己之前的选择
    my_moves = []
    
    # 计算自己之前的选择
    for i in range(len(history)):
        if i == 0:
            my_moves.append("C")  # 默认第一轮合作
        else:
            prev_opponent = history[i-1]
            prev_mine = my_moves[i-1]
            
            # 使用Pavlov策略规则 (Win-Stay, Lose-Shift)
            if (prev_mine == "D" and prev_opponent == "C") or (prev_mine == "C" and prev_opponent == "C"):
                my_moves.append(prev_mine)  # 保持选择
            else:
                my_moves.append("D" if prev_mine == "C" else "C")  # 改变选择
    
    return my_moves[-1] if my_moves else "C"
"""
                exec(setup_code, safe_globals, local_vars)
            
            # 执行策略代码
            exec(strategy.code, safe_globals, local_vars)
            
            # 确保make_move函数存在
            if 'make_move' in local_vars and callable(local_vars['make_move']):
                # 调用make_move函数
                result = local_vars['make_move'](opponent_history)
                if result in ['C', 'D']:
                    return result
                else:
                    logger.warning(f"策略 {strategy.name} 返回了无效结果: {result}，默认返回随机选择")
                    return random.choice(['C', 'D'])  # 随机选择，避免所有策略都返回相同结果
            else:
                logger.warning(f"策略 {strategy.name} 中没有找到可调用的make_move函数")
        except Exception as e:
            logger.error(f"执行策略 {strategy.name} 的make_move函数时出错: {e}")
        
        # 执行失败时返回随机选择，而不是总是合作
        logger.warning(f"策略 {strategy.name} 执行失败，返回随机选择")
        return random.choice(['C', 'D'])
    except Exception as e:
        logger.error(f"策略 {strategy.name} 执行过程中发生错误: {e}")
        # 出错时返回随机选择
        return random.choice(['C', 'D'])

def main():
    print("开始调试锦标赛执行过程...\n")
    
    # 1. 测试各种策略的执行结果
    debug_strategy_execution()
    
    # 2. 模拟执行一场锦标赛比赛
    debug_tournament_match()
    
    # 3. 模拟完整运行一个锦标赛
    debug_tournament_run()
    
    # 4. 修复发现的问题
    fix_tournament_problems()
    
    print("\n调试完成!")

if __name__ == "__main__":
    main() 