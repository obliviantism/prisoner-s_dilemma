#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试策略执行的简单脚本

这个脚本会:
1. 直接调用strategies.py中的execute_strategy函数
2. 输出不同策略的行为
3. 验证策略执行函数是否正常工作

用法:
python test_strategy_execution.py
"""

from dilemma_game.strategies import execute_strategy, get_all_strategies

def main():
    # 获取所有预设策略
    all_strategies = get_all_strategies()
    print(f"找到 {len(all_strategies)} 个预设策略\n")
    
    # 测试历史记录
    test_histories = [
        [],  # 空历史
        ['C'],  # 对手第一轮合作
        ['D'],  # 对手第一轮背叛
        ['C', 'C'],  # 对手连续合作
        ['D', 'D'],  # 对手连续背叛
    ]
    
    # 测试每个策略
    for strategy in all_strategies:
        print(f"\n策略: {strategy['name']} (ID: {strategy['id']})")
        print(f"描述: {strategy['description']}")
        
        for history in test_histories:
            history_str = "[]" if not history else str(history)
            try:
                choice = execute_strategy(strategy['id'], history.copy())
                print(f"  对手历史 {history_str} -> 选择 {choice}")
            except Exception as e:
                print(f"  错误: 对手历史 {history_str} -> 执行失败: {str(e)}")
    
    # 特别测试针锋相对策略
    print("\n\n特别测试 - 针锋相对策略与始终背叛策略对战 10 回合:")
    p1_history = []  # 针锋相对历史
    p2_history = []  # 始终背叛历史
    
    for round_num in range(10):
        p1_choice = execute_strategy('tit_for_tat', p2_history)
        p2_choice = execute_strategy('always_defect', p1_history)
        
        p1_history.append(p1_choice)
        p2_history.append(p2_choice)
        
        print(f"回合 {round_num+1}: 针锋相对选择 {p1_choice} vs 始终背叛选择 {p2_choice}")
    
    # 特别测试永不原谅策略
    print("\n\n特别测试 - 永不原谅策略与随机策略对战 10 回合:")
    p1_history = []  # 永不原谅历史
    p2_history = []  # 用来测试的历史 (模拟随机行为)
    test_sequence = ['C', 'C', 'D', 'C', 'C', 'C', 'C', 'C', 'C', 'C']
    
    for round_num in range(10):
        p1_choice = execute_strategy('grudger', p2_history)
        p2_choice = test_sequence[round_num]  # 模拟随机行为
        
        p1_history.append(p1_choice)
        p2_history.append(p2_choice)
        
        print(f"回合 {round_num+1}: 永不原谅选择 {p1_choice} vs 对手选择 {p2_choice}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 