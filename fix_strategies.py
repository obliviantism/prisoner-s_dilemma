#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复策略表中的数据
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from dilemma_game.models import Strategy
from dilemma_game.strategies import PRESET_STRATEGIES

def update_preset_strategies():
    """更新数据库中的预设策略信息"""
    print("开始更新预设策略...")
    
    # 建立策略名称到ID的映射
    preset_map = {}
    for strategy in PRESET_STRATEGIES:
        # 策略全名存在空格和括号，去掉英文部分，只保留中文名
        name = strategy['name']
        if ' (' in name:
            name = name.split(' (')[0]
        preset_map[name] = strategy['id']
        print(f"预设策略: {name} -> {strategy['id']}")
    
    # 更新数据库中的策略
    strategies = Strategy.objects.all()
    for strategy in strategies:
        # 尝试匹配策略名
        simple_name = strategy.name
        if ' (' in simple_name:
            simple_name = simple_name.split(' (')[0]
        
        preset_id = preset_map.get(simple_name)
        if preset_id:
            strategy.is_preset = True
            strategy.preset_id = preset_id
            strategy.save()
            print(f"已更新策略: {strategy.name} -> 预设ID: {preset_id}")
        else:
            print(f"未找到匹配: {strategy.name}")

if __name__ == "__main__":
    update_preset_strategies()
    print("更新完成!") 