"""
修复Q-learning策略的preset_id
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from django.contrib.auth.models import User
from dilemma_game.models import Strategy

def fix_q_learning_strategies():
    print("开始检查和修复Q-learning策略...")
    
    # 查找所有与Q-learning相关的策略
    q_strategies = Strategy.objects.filter(name__icontains='Q学习')
    o_strategies = Strategy.objects.filter(name__icontains='O学习')
    learning_strategies = Strategy.objects.filter(name__icontains='learning')
    
    # 输出所有找到的策略信息
    print("\nQ学习相关策略:")
    for s in q_strategies:
        print(f"ID: {s.id}, 名称: {s.name}, Preset ID: {s.preset_id}")
    
    print("\nO学习相关策略:")
    for s in o_strategies:
        print(f"ID: {s.id}, 名称: {s.name}, Preset ID: {s.preset_id}")
    
    print("\n含'Learning'的策略:")
    for s in learning_strategies:
        print(f"ID: {s.id}, 名称: {s.name}, Preset ID: {s.preset_id}")
    
    # 修复策略
    fixed_count = 0
    
    # 修复可能是Q-learning的策略
    all_potential_q_strategies = list(q_strategies) + list(o_strategies) + list(learning_strategies)
    for s in all_potential_q_strategies:
        # 如果是类似Q学习(O-Learning)这样的命名，修复preset_id
        if 'Q学习' in s.name or 'O学习' in s.name or ('学习' in s.name and ('Q' in s.name or 'O' in s.name)):
            old_preset_id = s.preset_id
            old_name = s.name
            
            # 修复preset_id
            s.preset_id = 'q_learning'
            
            # 修复名称中的O-Learning为Q-Learning
            if 'O-Learning' in s.name:
                s.name = s.name.replace('O-Learning', 'Q-Learning')
            elif 'O-learning' in s.name:
                s.name = s.name.replace('O-learning', 'Q-Learning')
            elif 'O_Learning' in s.name:
                s.name = s.name.replace('O_Learning', 'Q-Learning')
            elif 'O_learning' in s.name:
                s.name = s.name.replace('O_learning', 'Q-Learning')
                
            s.save()
            fixed_count += 1
            print(f"\n已修复策略: {old_name} -> {s.name}")
            print(f"Preset ID: {old_preset_id} -> {s.preset_id}")
    
    print(f"\n总计修复了 {fixed_count} 个策略")
    
    # 确认修复后的策略
    print("\n修复后的Q-learning策略:")
    for s in Strategy.objects.filter(preset_id='q_learning'):
        print(f"ID: {s.id}, 名称: {s.name}, Preset ID: {s.preset_id}")

if __name__ == '__main__':
    fix_q_learning_strategies()
    print("\n完成！请重启服务器并检查锦标赛结果页面，看是否显示Q-Learning分析按钮。") 