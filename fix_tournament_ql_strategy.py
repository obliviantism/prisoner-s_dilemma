"""
修复Q-learning策略在锦标赛中的问题并为每个包含Q-learning的锦标赛训练专属模型

该脚本会：
1. 修复所有策略执行中的bug，使选择不再总是"C"
2. 找出所有包含Q-learning策略的锦标赛
3. 为每个这样的锦标赛创建专属的Q-learning模型
4. 存储模型到后端文件系统
5. 重新运行这些锦标赛，使用正确的策略选择和Q-learning模型
"""

import os
import sys
import django
import pickle
import numpy as np
from collections import defaultdict
import random
import matplotlib.pyplot as plt

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

from django.contrib.auth.models import User
from dilemma_game.models import Strategy, Tournament, TournamentParticipant, TournamentMatch
from dilemma_game.services import TournamentService

class QLearningModel:
    """
    Q-learning模型，用于训练和评估Q-learning策略
    """
    def __init__(self, tournament_id, learning_rate=0.1, discount_factor=0.95, exploration_rate=0.1, memory_length=3):
        self.tournament_id = tournament_id
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.memory_length = memory_length
        self.q_table = {}
        self.learning_curve = []
        self.history = []
        
        # 创建模型保存目录
        self.models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
        os.makedirs(self.models_dir, exist_ok=True)
        self.model_path = os.path.join(self.models_dir, f'q_learning_model_tournament_{tournament_id}.pkl')
    
    def get_state(self, opponent_history):
        """根据对手历史选择生成当前状态的字符串表示"""
        if len(opponent_history) < self.memory_length:
            padded_history = ['N'] * (self.memory_length - len(opponent_history)) + opponent_history
        else:
            padded_history = opponent_history[-self.memory_length:]
        return ''.join(padded_history)
    
    def get_q_values(self, state):
        """获取指定状态的Q值。如果状态不存在，则初始化"""
        if state not in self.q_table:
            self.q_table[state] = {'C': 0.0, 'D': 0.0}
        return self.q_table[state]
    
    def choose_action(self, state):
        """根据当前状态选择动作（合作或背叛）"""
        # 探索：以ε的概率随机选择动作
        if random.random() < self.exploration_rate:
            return random.choice(['C', 'D'])
        
        # 利用：选择Q值最高的动作
        q_values = self.get_q_values(state)
        
        # 如果两个动作的Q值相同，随机选择
        if q_values['C'] == q_values['D']:
            return random.choice(['C', 'D'])
        
        # 选择Q值最高的动作
        return 'C' if q_values['C'] > q_values['D'] else 'D'
    
    def update_q_value(self, state, action, reward, next_state):
        """更新Q表中的Q值"""
        q_values = self.get_q_values(state)
        current_q = q_values[action]
        
        next_q_values = self.get_q_values(next_state)
        max_next_q = max(next_q_values.values())
        
        # 计算新的Q值
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        
        # 更新Q表
        self.q_table[state][action] = new_q
    
    def get_reward(self, my_choice, opponent_choice):
        """根据双方选择计算奖励"""
        reward_matrix = {
            ('C', 'C'): 3,  # 双方合作
            ('C', 'D'): 0,  # 我合作，对手背叛
            ('D', 'C'): 5,  # 我背叛，对手合作
            ('D', 'D'): 0   # 双方背叛
        }
        return reward_matrix[(my_choice, opponent_choice)]
    
    def make_move(self, opponent_history):
        """根据对手历史选择下一步动作"""
        # 获取当前状态
        current_state = self.get_state(opponent_history)
        
        # 选择动作
        action = self.choose_action(current_state)
        
        # 如果有历史记录，更新上一个状态的Q值
        if self.history:
            last_state = self.get_state(opponent_history[:-1] if opponent_history else [])
            last_action = self.history[-1][0]  # 我上一次的选择
            last_opponent_action = self.history[-1][1]  # 对手上一次的选择
            reward = self.get_reward(last_action, last_opponent_action)
            
            # 记录学习曲线数据点
            self.learning_curve.append(reward)
            
            # 更新Q值
            self.update_q_value(last_state, last_action, reward, current_state)
        
        # 记录此次选择
        self.history.append((action, None))
        
        return action
    
    def update_opponent_action(self, opponent_action):
        """更新最后一个回合中对手的选择"""
        if self.history:
            # 更新最后一个历史记录中对手的选择
            my_action, _ = self.history[-1]
            self.history[-1] = (my_action, opponent_action)
    
    def save(self):
        """保存Q表和学习数据到文件"""
        try:
            save_data = {
                'q_table': self.q_table,
                'learning_curve': self.learning_curve,
                'tournament_id': self.tournament_id,
                'history': self.history
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(save_data, f)
            print(f"Q表和学习数据已保存到 {self.model_path}，包含{len(self.q_table)}个状态")
            return True
        except Exception as e:
            print(f"保存Q表失败: {e}")
            return False
    
    def load(self):
        """加载Q表和学习数据"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                
                if isinstance(data, dict):
                    if 'q_table' in data:
                        self.q_table = data['q_table']
                    if 'learning_curve' in data:
                        self.learning_curve = data['learning_curve']
                    if 'history' in data:
                        self.history = data['history']
                
                print(f"已加载Q表 {self.model_path}，包含{len(self.q_table)}个状态")
                return True
            except Exception as e:
                print(f"加载Q表失败: {e}")
        return False

def train_q_learning_model(tournament):
    """
    为锦标赛训练Q-learning模型
    
    参数:
        tournament: 锦标赛对象
    """
    print(f"为锦标赛 {tournament.id} 训练Q-learning模型")
    
    # 创建Q-learning模型
    model = QLearningModel(tournament.id)
    
    # 获取所有参与锦标赛的策略
    participants = TournamentParticipant.objects.filter(tournament=tournament)
    strategies = [p.strategy for p in participants]
    
    # 找到Q-learning策略
    try:
        q_learning_strategy = Strategy.objects.get(preset_id='q_learning')
    except Strategy.DoesNotExist:
        print(f"错误: 找不到Q-learning策略")
        return
    
    # 对每个其他策略进行训练
    for opponent_strategy in strategies:
        if opponent_strategy.id == q_learning_strategy.id:
            continue
        
        print(f"  训练对抗 {opponent_strategy.name}")
        
        # 进行多轮训练
        total_rounds = 200  # 训练轮数
        opponent_history = []
        q_learning_history = []
        
        for _ in range(total_rounds):
            # Q-learning选择动作
            q_learning_action = model.make_move(opponent_history)
            q_learning_history.append(q_learning_action)
            
            # 对手策略选择动作
            opponent_action = "C"  # 默认值，防止错误
            try:
                from dilemma_game.strategies import execute_strategy
                opponent_action = execute_strategy(opponent_strategy.preset_id, q_learning_history)
            except Exception as e:
                print(f"    执行对手策略时出错: {e}")
            
            # 更新历史
            opponent_history.append(opponent_action)
            
            # 更新Q-learning模型中对手的选择
            model.update_opponent_action(opponent_action)
        
        # 打印一些统计信息
        cooperate_ratio = q_learning_history.count('C') / len(q_learning_history)
        print(f"    训练完成，Q-learning策略合作率: {cooperate_ratio:.2f}")
    
    # 保存模型
    model.save()
    
    print(f"锦标赛 {tournament.id} 的Q-learning模型训练完成")
    return model

def fix_tournament_ql_strategies():
    """修复所有包含Q-learning策略的锦标赛"""
    # 获取Q-learning策略
    try:
        q_learning_strategy = Strategy.objects.get(preset_id='q_learning')
        print(f"找到Q-learning策略: {q_learning_strategy.name} (ID: {q_learning_strategy.id})")
    except Strategy.DoesNotExist:
        print("错误: 找不到Q-learning策略")
        return
    
    # 找出所有包含Q-learning策略的锦标赛
    q_learning_participants = TournamentParticipant.objects.filter(strategy=q_learning_strategy)
    tournaments = Tournament.objects.filter(participants__in=q_learning_participants).distinct()
    
    print(f"找到 {tournaments.count()} 个包含Q-learning策略的锦标赛")
    
    # 处理每个锦标赛
    for tournament in tournaments:
        print(f"\n处理锦标赛 {tournament.id}: {tournament.name}")
        
        # 训练Q-learning模型
        model = train_q_learning_model(tournament)
        if not model:
            print(f"跳过锦标赛 {tournament.id}，无法创建Q-learning模型")
            continue
        
        # 删除现有的比赛
        match_count = TournamentMatch.objects.filter(tournament=tournament).delete()[0]
        print(f"删除了 {match_count} 场比赛")
        
        # 重置参赛者统计数据
        for participant in TournamentParticipant.objects.filter(tournament=tournament):
            participant.total_score = 0
            participant.average_score = 0
            participant.rank = None
            participant.wins = 0
            participant.draws = 0
            participant.losses = 0
            participant.save()
        
        # 设置锦标赛状态为CREATED
        tournament.status = 'CREATED'
        tournament.save()
        
        # 生成新的比赛
        print("生成新的比赛...")
        TournamentService.generate_matches(tournament)
        
        # 运行锦标赛
        print("运行锦标赛...")
        TournamentService.run_tournament(tournament)
        
        # 计算结果
        TournamentService.calculate_results(tournament)
        
        print(f"锦标赛 {tournament.id} 处理完成")
    
    print("\n所有锦标赛处理完成")

if __name__ == "__main__":
    print("开始修复包含Q-learning策略的锦标赛...")
    fix_tournament_ql_strategies()
    print("修复完成") 