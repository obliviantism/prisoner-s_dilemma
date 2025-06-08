"""
综合修复Q-Learning相关问题的脚本

1. 修复所有Q-Learning策略的preset_id
2. 确保Q-Learning模型文件存在
3. 检查特定锦标赛中的Q-Learning策略
"""

import os
import django
import sys
import argparse
import pickle
from collections import defaultdict

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from django.contrib.auth.models import User
from dilemma_game.models import Strategy, Tournament, TournamentParticipant
from django.db.models import Q

def fix_all_strategies():
    """修复所有Q-Learning策略的preset_id"""
    print("\n1. 修复所有Q-Learning策略...")
    
    # 查找所有与Q-learning相关的策略
    strategies = Strategy.objects.filter(
        Q(name__icontains='Q学习') | 
        Q(name__icontains='Q-Learning') |
        Q(name__icontains='Q-learning') |
        Q(name__icontains='O学习') |
        Q(name__icontains='learning')
    )
    
    print(f"找到 {strategies.count()} 个可能的Q-Learning策略:")
    
    fixed_count = 0
    for strategy in strategies:
        print(f"\n  ID: {strategy.id}")
        print(f"  名称: {strategy.name}")
        print(f"  当前Preset ID: {strategy.preset_id or '无'}")
        
        # 修复preset_id
        old_preset_id = strategy.preset_id
        strategy.preset_id = 'q_learning'
        strategy.is_preset = True
        strategy.save()
        
        fixed_count += 1
        print(f"  已更新: Preset ID -> 'q_learning'")
    
    print(f"\n总共修复了 {fixed_count} 个Q-Learning策略")

def fix_tournament_strategies(tournament_id):
    """修复特定锦标赛中的Q-Learning策略"""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
    except Tournament.DoesNotExist:
        print(f"错误: 找不到ID为 {tournament_id} 的锦标赛")
        return
    
    print(f"\n2. 修复锦标赛 '{tournament.name}' (ID={tournament_id}) 中的Q-Learning策略...")
    
    # 查找所有参赛者
    participants = TournamentParticipant.objects.filter(tournament=tournament)
    print(f"该锦标赛有 {participants.count()} 名参赛者")
    
    # 查找可能是Q-Learning的策略
    q_learning_fixed = False
    for p in participants:
        strategy = p.strategy
        strategy_name = strategy.name
        
        # 检查是否有'Q学习', 'Q-Learning', 'Q-learning', 'O学习'或'q_learning'的名称,或者包含"learning"
        if ('Q学习' in strategy_name or 
            'Q-Learning' in strategy_name or 
            'Q-learning' in strategy_name or 
            'O学习' in strategy_name or 
            'learning' in strategy_name.lower()):
            
            print(f"\n找到可能的Q-Learning策略:")
            print(f"  ID: {strategy.id}")
            print(f"  名称: {strategy_name}")
            print(f"  当前Preset ID: {strategy.preset_id or '无'}")
            
            # 修复preset_id
            old_preset_id = strategy.preset_id
            strategy.preset_id = 'q_learning'
            strategy.is_preset = True
            strategy.save()
            
            print(f"  已更新: Preset ID -> 'q_learning'")
            q_learning_fixed = True
    
    # 确认修复后锦标赛中的Q-learning策略
    q_learning_participants = TournamentParticipant.objects.filter(
        tournament=tournament,
        strategy__preset_id='q_learning'
    )
    
    print(f"\n修复后锦标赛中的Q-learning策略数量: {q_learning_participants.count()}")
    for p in q_learning_participants:
        print(f"  策略名称: {p.strategy.name}")
        print(f"  Preset ID: {p.strategy.preset_id}")

def create_q_model():
    """创建Q-Learning模型文件"""
    print("\n3. 检查和创建Q-Learning模型文件...")
    
    model_path = os.path.join('models', 'q_learning_model.pkl')
    model_dir = os.path.dirname(model_path)
    
    # 确保models目录存在
    if not os.path.exists(model_dir):
        print(f"models目录不存在，创建该目录...")
        os.makedirs(model_dir)
        print(f"已创建目录: {model_dir}")
    else:
        print(f"models目录已存在: {model_dir}")
    
    # 检查模型文件是否存在
    if os.path.exists(model_path) and os.path.getsize(model_path) > 0:
        print(f"模型文件已存在: {model_path}")
        print(f"文件大小: {os.path.getsize(model_path)} 字节")
        
        # 尝试读取文件以验证格式
        try:
            with open(model_path, 'rb') as f:
                q_table = pickle.load(f)
            print(f"成功加载Q表，包含 {len(q_table)} 个状态")
        except Exception as e:
            print(f"警告: 无法读取现有模型文件: {str(e)}")
            print("将创建新的模型文件...")
            create_new_model(model_path)
    else:
        print(f"模型文件不存在或为空: {model_path}")
        create_new_model(model_path)

def create_new_model(model_path):
    """创建新的Q-Learning模型文件"""
    # 创建一个示例Q表
    q_table = defaultdict(lambda: {'C': 0, 'D': 0})
    
    # 为一些常见状态填充Q值
    q_table['CCC'] = {'C': 3.0, 'D': 5.0}
    q_table['CCD'] = {'C': 1.5, 'D': 3.0}
    q_table['CDC'] = {'C': 2.0, 'D': 4.0}
    q_table['CDD'] = {'C': 0.5, 'D': 2.0}
    q_table['DCC'] = {'C': 2.5, 'D': 4.5}
    q_table['DCD'] = {'C': 1.0, 'D': 2.5}
    q_table['DDC'] = {'C': 1.5, 'D': 3.5}
    q_table['DDD'] = {'C': 0.0, 'D': 1.0}
    q_table['CC'] = {'C': 2.8, 'D': 4.8}
    q_table['CD'] = {'C': 1.2, 'D': 2.8}
    q_table['DC'] = {'C': 2.2, 'D': 4.0}
    q_table['DD'] = {'C': 0.2, 'D': 1.5}
    q_table['C'] = {'C': 2.5, 'D': 4.5}
    q_table['D'] = {'C': 0.8, 'D': 2.0}
    q_table[''] = {'C': 1.5, 'D': 3.0}
    
    # 保存为普通dict而不是defaultdict
    q_table_dict = dict()
    for k, v in q_table.items():
        q_table_dict[k] = v
    
    # 保存Q表
    with open(model_path, 'wb') as f:
        pickle.dump(q_table_dict, f)
    
    print(f"已创建新的Q-Learning模型文件: {model_path}")
    print(f"包含 {len(q_table)} 个状态的Q值")

def show_tournaments():
    """显示所有锦标赛"""
    print("\n系统中的锦标赛列表:")
    tournaments = Tournament.objects.all().order_by('-created_at')
    for t in tournaments:
        print(f"ID: {t.id}, 名称: {t.name}, 创建时间: {t.created_at}, 状态: {t.status}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='修复Q-Learning相关问题')
    parser.add_argument('-t', '--tournament', type=int, help='指定要修复的锦标赛ID')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有锦标赛')
    parser.add_argument('--all', action='store_true', help='修复所有Q-Learning相关问题')
    
    args = parser.parse_args()
    
    if args.list:
        show_tournaments()
        sys.exit(0)
    
    if args.tournament:
        fix_tournament_strategies(args.tournament)
    else:
        fix_all_strategies()
    
    # 始终创建/检查模型文件
    create_q_model()
    
    print("\n完成！请重启服务器并检查锦标赛结果页面，看是否显示Q-Learning分析按钮。") 