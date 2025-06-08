"""
添加Q-learning预设策略到数据库
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

def add_q_learning_strategy():
    print("正在添加Q-learning策略到数据库...")
    
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
    
    # 查找Q-learning预设策略
    q_learning_preset = None
    for preset in PRESET_STRATEGIES:
        if preset['id'] == 'q_learning':
            q_learning_preset = preset
            break
    
    if not q_learning_preset:
        print("错误：在预设策略列表中找不到Q-learning策略")
        return
    
    # 检查Q-learning策略是否已存在
    existing_strategy = Strategy.objects.filter(preset_id='q_learning').first()
    if existing_strategy:
        print(f"Q-learning策略已存在: {existing_strategy.name}")
        return
    
    # 创建Q-learning策略
    strategy = Strategy.objects.create(
        name=q_learning_preset['name'],
        description=q_learning_preset['description'],
        code=q_learning_preset['code'],
        created_by=admin_user,
        is_preset=True,
        preset_id='q_learning'
    )
    
    print(f"成功创建Q-learning策略: {strategy.name}")

if __name__ == '__main__':
    add_q_learning_strategy() 