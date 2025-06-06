#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
调试锦标赛执行问题
"""

import os
import sys
import django
import json
from collections import defaultdict

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from dilemma_game.models import Tournament, TournamentParticipant, TournamentMatch, Strategy
from dilemma_game.services import TournamentService, GameService
from dilemma_game.strategies import PRESET_STRATEGIES, execute_strategy

def test_strategy_execution():
    """测试每个策略的执行情况"""
    print("\n===== 策略执行测试 =====")
    
    # 获取所有策略
    strategies = Strategy.objects.all()
    print(f"找到 {strategies.count()} 个策略")
    
    # 测试历史
    test_histories = [
        [],                     # 空历史
        ['C'],                  # 一次合作
        ['D'],                  # 一次背叛
        ['C', 'C', 'C'],        # 连续合作
        ['D', 'D', 'D'],        # 连续背叛
        ['C', 'D', 'C', 'D']    # 交替
    ]
    
    results = {}
    
    # 测试每个策略
    for strategy in strategies:
        print(f"\n策略: {strategy.name} (ID: {strategy.id})")
        print(f"预设: {'是' if strategy.is_preset else '否'}, 预设ID: {strategy.preset_id or 'None'}")
        results[strategy.name] = []
        
        for history in test_histories:
            history_str = str(history)
            choice = GameService.execute_strategy(strategy, history.copy())
            results[strategy.name].append(choice)
            print(f"  历史 {history_str} -> 选择 {choice}")
    
    # 分析策略多样性
    print("\n策略多样性分析:")
    for i, history in enumerate(test_histories):
        history_str = str(history)
        choices = [results[s.name][i] for s in strategies]
        c_count = choices.count('C')
        d_count = choices.count('D')
        print(f"对于历史 {history_str}: C={c_count}, D={d_count}")
    
    # 确认是否有多样性
    strategy_patterns = defaultdict(list)
    for strategy in strategies:
        pattern = ''.join(results[strategy.name])
        strategy_patterns[pattern].append(strategy.name)
    
    print("\n策略分组 (根据相同的决策模式):")
    for pattern, strat_names in strategy_patterns.items():
        print(f"模式 {pattern}: {', '.join(strat_names)}")
    
    if len(strategy_patterns) == 1:
        print("\n警告: 所有策略表现一致，这是问题所在!")
    else:
        print(f"\n检测到 {len(strategy_patterns)} 种不同的策略模式")

def test_match_execution():
    """测试一场比赛的执行"""
    print("\n===== 比赛执行测试 =====")
    
    # 获取一个进行中的锦标赛
    tournament = Tournament.objects.filter(status='IN_PROGRESS').first()
    if not tournament:
        tournament = Tournament.objects.filter(status='COMPLETED').first()
        if not tournament:
            print("没有找到可用的锦标赛")
            return
    
    print(f"使用锦标赛: {tournament.name} (状态: {tournament.status})")
    
    # 获取两个不同的策略
    participants = TournamentParticipant.objects.filter(tournament=tournament)
    if participants.count() < 2:
        print("参赛者数量不足")
        return
    
    p1 = participants[0]
    p2 = participants[1]
    
    print(f"策略1: {p1.strategy.name}")
    print(f"策略2: {p2.strategy.name}")
    
    # 创建一个测试比赛
    match = TournamentMatch(
        tournament=tournament,
        participant1=p1,
        participant2=p2,
        repetition=999,  # 使用特殊值表示测试
        status='PENDING'
    )
    
    # 修补策略执行函数记录结果
    orig_execute = GameService.execute_strategy
    
    def monitored_execute(strategy, opponent_history):
        result = orig_execute(strategy, opponent_history)
        print(f"策略 {strategy.name} 对历史 {opponent_history} 选择: {result}")
        return result
    
    # 替换函数
    GameService.execute_strategy = monitored_execute
    
    try:
        # 模拟执行10轮
        print("\n模拟执行10轮:")
        p1_history = []
        p2_history = []
        p1_score = 0
        p2_score = 0
        
        payoff_matrix = tournament.payoff_matrix
        print(f"收益矩阵: {payoff_matrix}")
        
        # 定义根据自定义收益矩阵计算分数的函数
        def calculate_scores(p1_choice: str, p2_choice: str):
            key = p1_choice + p2_choice
            mapped_key = {
                'CC': 'CC',
                'CD': 'CD',
                'DC': 'DC',
                'DD': 'DD'
            }.get(key)
            
            return tuple(payoff_matrix[mapped_key])
        
        for round_num in range(1, 11):
            # 执行策略获取选择
            p1_choice = GameService.execute_strategy(p1.strategy, p2_history)
            p2_choice = GameService.execute_strategy(p2.strategy, p1_history)
            
            # 计算分数
            round_p1_score, round_p2_score = calculate_scores(p1_choice, p2_choice)
            
            print(f"回合 {round_num}: {p1.strategy.name}选择{p1_choice}, {p2.strategy.name}选择{p2_choice}")
            print(f"  得分: {p1.strategy.name}={round_p1_score}, {p2.strategy.name}={round_p2_score}")
            
            # 更新历史和总分
            p1_history.append(p1_choice)
            p2_history.append(p2_choice)
            p1_score += round_p1_score
            p2_score += round_p2_score
        
        print(f"\n最终得分: {p1.strategy.name}={p1_score}, {p2.strategy.name}={p2_score}")
        
    finally:
        # 恢复原始函数
        GameService.execute_strategy = orig_execute

if __name__ == "__main__":
    print("开始调试锦标赛执行情况...")
    
    # 测试策略执行
    test_strategy_execution()
    
    # 测试比赛执行
    test_match_execution()
    
    print("\n调试完成") 