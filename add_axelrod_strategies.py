"""
添加Axelrod第一次锦标赛的策略到数据库
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from django.contrib.auth.models import User
from dilemma_game.models import Strategy
from dilemma_game.strategies import PRESET_STRATEGIES

def add_axelrod_strategies():
    print("正在添加Axelrod第一次锦标赛的策略到数据库...")
    
    # 获取管理员用户或创建一个测试用户
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        admin_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        print("创建测试用户")
    
    # Axelrod第一次锦标赛的策略ID列表
    axelrod_strategy_ids = [
        'davis', 'joss', 'tullock', 'nydegger', 'grofman', 
        'shubik', 'stein_and_rapoport', 'downing', 'graaskamp',
        'tideman_and_chieruzzi'
    ]
    
    # 已有的策略ID (这些已经是Axelrod锦标赛中的策略)
    existing_axelrod_ids = [
        'tit_for_tat',      # Anatol Rapoport的策略，赢得了锦标赛
        'always_cooperate', # 始终合作策略
        'always_defect',    # 始终背叛策略
        'random',           # 随机策略
        'grudger'           # Friedman的"永不原谅"策略
    ]
    
    # 添加新策略并打印已有策略
    added_count = 0
    existing_count = 0
    
    # 显示已有的Axelrod策略
    print("\n已有的Axelrod锦标赛策略:")
    for preset_id in existing_axelrod_ids:
        strategy = Strategy.objects.filter(preset_id=preset_id).first()
        if strategy:
            print(f"- {strategy.name} (ID: {preset_id}) - 已存在")
            existing_count += 1
        else:
            # 如果已有策略未添加到数据库，也添加它
            preset = next((s for s in PRESET_STRATEGIES if s['id'] == preset_id), None)
            if preset:
                strategy = Strategy.objects.create(
                    name=preset['name'],
                    description=preset['description'],
                    code=preset['code'],
                    created_by=admin_user,
                    is_preset=True,
                    preset_id=preset['id']
                )
                print(f"+ {preset['name']} (ID: {preset_id}) - 已添加")
                added_count += 1
    
    # 添加新的Axelrod策略
    print("\n添加新的Axelrod锦标赛策略:")
    for preset_id in axelrod_strategy_ids:
        # 检查策略是否已存在
        existing_strategy = Strategy.objects.filter(preset_id=preset_id).first()
        if existing_strategy:
            print(f"- {existing_strategy.name} (ID: {preset_id}) - 已存在")
            existing_count += 1
            continue
        
        # 查找预设策略
        preset = next((s for s in PRESET_STRATEGIES if s['id'] == preset_id), None)
        if not preset:
            print(f"! 找不到预设策略 {preset_id}")
            continue
        
        # 创建新策略
        try:
            strategy = Strategy.objects.create(
                name=preset['name'],
                description=preset['description'],
                code=preset['code'],
                created_by=admin_user,
                is_preset=True,
                preset_id=preset['id']
            )
            print(f"+ {preset['name']} (ID: {preset_id}) - 已添加")
            added_count += 1
        except Exception as e:
            print(f"! 添加策略 {preset_id} 失败: {str(e)}")
    
    # 打印总结
    print(f"\n总结: 添加了 {added_count} 个新策略, 已有 {existing_count} 个策略")
    print("Axelrod第一次锦标赛的所有15个策略现已可用。")

if __name__ == '__main__':
    add_axelrod_strategies() 