#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查所有策略行为的脚本

这个脚本会:
1. 测试所有策略在不同历史输入下的行为
2. 对比它们的决策模式
3. 验证策略实现是否与预期一致

使用方法:
python check_strategies.py
"""

import os
import sys
import django
from collections import defaultdict

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from dilemma_game.models import Strategy
from dilemma_game.services import GameService
from dilemma_game.strategies import get_all_strategies, execute_strategy

def check_db_strategies():
    """测试数据库中所有策略的行为"""
    print("\n===== 数据库策略行为测试 =====")
    
    # 获取所有策略
    strategies = Strategy.objects.all()
    
    if not strategies:
        print("数据库中没有找到策略!")
        return {}
    
    print(f"找到 {strategies.count()} 个策略")
    
    # 创建测试历史记录
    test_histories = [
        [],  # 空历史，第一轮
        ['C'],  # 对手第一轮合作
        ['D'],  # 对手第一轮背叛
        ['C', 'C'],  # 对手连续合作
        ['D', 'D'],  # 对手连续背叛
        ['C', 'D', 'C'],  # 混合历史
        ['D', 'C', 'D'],   # 另一种混合历史
        ['C'] * 10,  # 对手总是合作
        ['D'] * 10,  # 对手总是背叛
        ['C', 'D'] * 5,  # 对手交替合作/背叛
        ['D', 'C'] * 5   # 对手交替背叛/合作
    ]
    
    results = {}
    
    # 测试每个策略
    for strategy in strategies:
        results[strategy.name] = []
        print(f"\n策略: {strategy.name}")
        
        for history in test_histories:
            history_str = "[]" if not history else str(history)
            try:
                choice = GameService.execute_strategy(strategy, history.copy())
                results[strategy.name].append(choice)
                print(f"  对手历史 {history_str} -> 选择 {choice}")
            except Exception as e:
                print(f"  错误: 对手历史 {history_str} -> 执行失败: {str(e)}")
                results[strategy.name].append('E')  # E表示错误
    
    # 分析策略多样性
    print("\n策略多样性分析:")
    for i, history in enumerate(test_histories):
        history_str = "[]" if not history else str(history)
        choices = [results[s.name][i] for s in strategies]
        c_count = choices.count('C')
        d_count = choices.count('D')
        e_count = choices.count('E')
        print(f"对于历史 {history_str}: C={c_count}, D={d_count}, 错误={e_count}")
    
    # 确认是否有多样性
    strategy_patterns = defaultdict(list)
    for strategy in strategies:
        pattern = ''.join(results[strategy.name])
        strategy_patterns[pattern].append(strategy.name)
    
    print("\n策略分组 (根据相同的决策模式):")
    for pattern, strat_names in strategy_patterns.items():
        print(f"模式 {pattern}: {', '.join(strat_names)}")
    
    if len(strategy_patterns) == 1:
        print("\n警告: 所有策略表现一致，这可能是问题所在!")
    else:
        print(f"\n检测到 {len(strategy_patterns)} 种不同的策略模式，这表明策略行为多样")
    
    return results

def check_preset_strategies():
    """测试预设策略的行为"""
    print("\n===== 预设策略行为测试 =====")
    
    # 获取所有预设策略
    preset_strategies = get_all_strategies()
    
    if not preset_strategies:
        print("没有找到预设策略!")
        return {}
    
    print(f"找到 {len(preset_strategies)} 个预设策略")
    
    # 创建测试历史记录
    test_histories = [
        [],  # 空历史，第一轮
        ['C'],  # 对手第一轮合作
        ['D'],  # 对手第一轮背叛
        ['C', 'C'],  # 对手连续合作
        ['D', 'D'],  # 对手连续背叛
        ['C', 'D', 'C'],  # 混合历史
        ['D', 'C', 'D']   # 另一种混合历史
    ]
    
    results = {}
    
    # 测试每个预设策略
    for strategy in preset_strategies:
        strategy_id = strategy['id']
        results[strategy['name']] = []
        print(f"\n预设策略: {strategy['name']} (ID: {strategy_id})")
        
        for history in test_histories:
            history_str = "[]" if not history else str(history)
            try:
                choice = execute_strategy(strategy_id, history.copy())
                results[strategy['name']].append(choice)
                print(f"  对手历史 {history_str} -> 选择 {choice}")
            except Exception as e:
                print(f"  错误: 对手历史 {history_str} -> 执行失败: {str(e)}")
                results[strategy['name']].append('E')  # E表示错误
    
    # 分析策略多样性
    print("\n预设策略多样性分析:")
    for i, history in enumerate(test_histories):
        history_str = "[]" if not history else str(history)
        choices = [results[s['name']][i] for s in preset_strategies]
        c_count = choices.count('C')
        d_count = choices.count('D')
        e_count = choices.count('E')
        print(f"对于历史 {history_str}: C={c_count}, D={d_count}, 错误={e_count}")
    
    # 确认是否有多样性
    strategy_patterns = defaultdict(list)
    for strategy in preset_strategies:
        pattern = ''.join(results[strategy['name']])
        strategy_patterns[pattern].append(strategy['name'])
    
    print("\n预设策略分组 (根据相同的决策模式):")
    for pattern, strat_names in strategy_patterns.items():
        print(f"模式 {pattern}: {', '.join(strat_names)}")
    
    if len(strategy_patterns) == 1:
        print("\n警告: 所有预设策略表现一致，这可能是问题所在!")
    else:
        print(f"\n检测到 {len(strategy_patterns)} 种不同的预设策略模式，这表明策略行为多样")
    
    return results

def main():
    try:
        # 测试数据库中的策略
        db_results = check_db_strategies()
        
        # 测试预设策略
        preset_results = check_preset_strategies()
        
        print("\n检查完成!")
        return True
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 