#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查services.py中的关键代码，查找可能导致所有比赛平局的问题
"""

import os
import sys
import django
import inspect

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from dilemma_game.services import TournamentService, GameService

def check_key_methods():
    """检查关键方法的实现"""
    
    print("检查TournamentService.play_match方法...")
    
    # 获取play_match方法的源代码
    play_match_source = inspect.getsource(TournamentService.play_match)
    
    # 查找calculate_scores函数定义
    if "def calculate_scores" in play_match_source:
        # 提取calculate_scores函数的代码
        start_idx = play_match_source.find("def calculate_scores")
        end_idx = play_match_source.find("return", start_idx)
        end_idx = play_match_source.find("\n", end_idx) + 1
        
        calc_scores_code = play_match_source[start_idx:end_idx]
        print("\n计分函数代码:")
        print(calc_scores_code)
        
        # 检查是否有硬编码的值
        if "DD" in calc_scores_code and "[1, 1]" in calc_scores_code:
            print("\n发现问题: 收益矩阵中的DD值在代码中被硬编码为[1, 1]")
            print("这将覆盖锦标赛对象中设置的值，导致所有比赛为平局")
            print("\n需要修改services.py文件中的代码")
        else:
            print("\n没有发现硬编码的[1, 1]值")
    
    # 检查calculate_results方法
    print("\n检查TournamentService.calculate_results方法...")
    calc_results_source = inspect.getsource(TournamentService.calculate_results)
    
    # 检查胜负平计算逻辑
    win_check = "match.player1_score > match.player2_score"
    loss_check = "match.player1_score < match.player2_score"
    
    if win_check in calc_results_source and loss_check in calc_results_source:
        print("胜负判定逻辑正常")
    else:
        print("警告: 胜负判定逻辑可能有问题")
    
    # 检查策略执行
    print("\n检查GameService.execute_strategy方法...")
    exec_strategy_source = inspect.getsource(GameService.execute_strategy)
    print(f"策略执行方法长度: {len(exec_strategy_source)} 字符")
    
    # 提取关键部分
    if "exec_strategy" in exec_strategy_source:
        print("策略执行使用了预定义的策略模块")
    else:
        print("警告: 没有找到预定义策略模块的调用")

def main():
    print("开始检查锦标赛服务代码...\n")
    check_key_methods()
    print("\n检查完成")

if __name__ == "__main__":
    main() 