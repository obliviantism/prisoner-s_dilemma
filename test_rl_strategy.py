"""
测试强化学习策略在囚徒困境中的表现
此脚本对比Q-learning策略与其他经典策略的表现
"""

import matplotlib.pyplot as plt
import numpy as np
from rl_strategy import QLearningStrategy
import os
import pickle

# 定义经典策略
class AlwaysCooperate:
    """始终合作策略"""
    def __init__(self):
        self.name = "Always Cooperate"
        self.history = []
        self.score = 0
    
    def make_move(self, opponent_history):
        action = 'C'
        self.history.append((action, None))
        return action
    
    def update_opponent_action(self, opponent_action):
        if self.history:
            my_action, _ = self.history[-1]
            self.history[-1] = (my_action, opponent_action)
            # 更新得分
            reward_matrix = {
                ('C', 'C'): 3,  # 双方合作
                ('C', 'D'): 0,  # 我合作，对手欺骗
                ('D', 'C'): 5,  # 我欺骗，对手合作
                ('D', 'D'): 0   # 双方欺骗
            }
            self.score += reward_matrix[(my_action, opponent_action)]

class AlwaysDefect:
    """始终欺骗策略"""
    def __init__(self):
        self.name = "Always Defect"
        self.history = []
        self.score = 0
    
    def make_move(self, opponent_history):
        action = 'D'
        self.history.append((action, None))
        return action
    
    def update_opponent_action(self, opponent_action):
        if self.history:
            my_action, _ = self.history[-1]
            self.history[-1] = (my_action, opponent_action)
            # 更新得分
            reward_matrix = {
                ('C', 'C'): 3,  # 双方合作
                ('C', 'D'): 0,  # 我合作，对手欺骗
                ('D', 'C'): 5,  # 我欺骗，对手合作
                ('D', 'D'): 0   # 双方欺骗
            }
            self.score += reward_matrix[(my_action, opponent_action)]

class TitForTat:
    """一报还一报策略"""
    def __init__(self):
        self.name = "Tit for Tat"
        self.history = []
        self.score = 0
    
    def make_move(self, opponent_history):
        if not opponent_history:
            action = 'C'  # 第一轮合作
        else:
            action = opponent_history[-1]  # 模仿对手上一轮的选择
        
        self.history.append((action, None))
        return action
    
    def update_opponent_action(self, opponent_action):
        if self.history:
            my_action, _ = self.history[-1]
            self.history[-1] = (my_action, opponent_action)
            # 更新得分
            reward_matrix = {
                ('C', 'C'): 3,  # 双方合作
                ('C', 'D'): 0,  # 我合作，对手欺骗
                ('D', 'C'): 5,  # 我欺骗，对手合作
                ('D', 'D'): 0   # 双方欺骗
            }
            self.score += reward_matrix[(my_action, opponent_action)]

class Random:
    """随机策略"""
    def __init__(self):
        self.name = "Random"
        self.history = []
        self.score = 0
        import random
        self.random = random
    
    def make_move(self, opponent_history):
        action = self.random.choice(['C', 'D'])
        self.history.append((action, None))
        return action
    
    def update_opponent_action(self, opponent_action):
        if self.history:
            my_action, _ = self.history[-1]
            self.history[-1] = (my_action, opponent_action)
            # 更新得分
            reward_matrix = {
                ('C', 'C'): 3,  # 双方合作
                ('C', 'D'): 0,  # 我合作，对手欺骗
                ('D', 'C'): 5,  # 我欺骗，对手合作
                ('D', 'D'): 0   # 双方欺骗
            }
            self.score += reward_matrix[(my_action, opponent_action)]

class GradualTFT:
    """渐进式一报还一报策略"""
    def __init__(self):
        self.name = "Gradual TFT"
        self.history = []
        self.score = 0
        self.defect_count = 0
        self.retaliation_mode = False
        self.forgiveness_count = 0
        
    def make_move(self, opponent_history):
        if not opponent_history:
            action = 'C'  # 第一轮合作
        elif self.retaliation_mode:
            # 在报复模式
            if self.defect_count > 0:
                # 继续报复
                action = 'D'
                self.defect_count -= 1
            else:
                # 报复结束，进入宽恕阶段
                self.retaliation_mode = False
                self.forgiveness_count = 2  # 两轮宽恕
                action = 'C'
        elif self.forgiveness_count > 0:
            # 在宽恕阶段
            action = 'C'
            self.forgiveness_count -= 1
        elif opponent_history[-1] == 'D':
            # 对手欺骗，开始报复
            self.retaliation_mode = True
            self.defect_count = len([x for x in opponent_history if x == 'D'])  # 报复次数等于对手欺骗总次数
            action = 'D'
        else:
            # 对手合作，也合作
            action = 'C'
        
        self.history.append((action, None))
        return action
    
    def update_opponent_action(self, opponent_action):
        if self.history:
            my_action, _ = self.history[-1]
            self.history[-1] = (my_action, opponent_action)
            # 更新得分
            reward_matrix = {
                ('C', 'C'): 3,  # 双方合作
                ('C', 'D'): 0,  # 我合作，对手欺骗
                ('D', 'C'): 5,  # 我欺骗，对手合作
                ('D', 'D'): 0   # 双方欺骗
            }
            self.score += reward_matrix[(my_action, opponent_action)]

def play_game(strategy1, strategy2, rounds=200, reset=True):
    """
    模拟两个策略之间的对弈
    
    参数:
        strategy1: 第一个策略
        strategy2: 第二个策略
        rounds: 回合数
        reset: 是否重置策略的历史和得分
    
    返回:
        两个策略的得分
    """
    if reset:
        strategy1.history = []
        strategy2.history = []
        strategy1.score = 0
        strategy2.score = 0
    
    s1_history = []  # 策略1历史选择
    s2_history = []  # 策略2历史选择
    
    for _ in range(rounds):
        # 获取两个策略的选择
        s1_choice = strategy1.make_move(s2_history)
        s2_choice = strategy2.make_move(s1_history)
        
        # 更新历史
        s1_history.append(s1_choice)
        s2_history.append(s2_choice)
        
        # 通知策略对手的选择
        strategy1.update_opponent_action(s2_choice)
        strategy2.update_opponent_action(s1_choice)
    
    return strategy1.score, strategy2.score

def save_results(results, filename="rl_tournament_results.pkl"):
    """保存结果到文件"""
    with open(filename, 'wb') as f:
        pickle.dump(results, f)
    print(f"结果已保存到 {filename}")

def load_results(filename="rl_tournament_results.pkl"):
    """从文件加载结果"""
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    return None

import random
exact_round = random.randint(500, 600)

def tournament(strategies, rounds=exact_round, iterations=10):
    """
    进行多次对弈的锦标赛，评估策略性能
    
    参数:
        strategies: 策略列表
        rounds: 每场对弈的回合数
        iterations: 重复次数，增加统计可靠性
    
    返回:
        锦标赛结果字典
    """
    # 创建结果矩阵
    n = len(strategies)
    total_scores = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            if i == j:
                continue  # 跳过自己对自己
            
            for _ in range(iterations):
                score_i, score_j = play_game(strategies[i], strategies[j], rounds)
                total_scores[i, j] += score_i
                total_scores[j, i] += score_j
    
    # 计算平均得分
    average_scores = total_scores / iterations
    
    # 计算每个策略的总分数和平均分数
    strategy_total_scores = np.sum(average_scores, axis=1)
    strategy_names = [s.name for s in strategies]
    
    # 构建结果字典
    results = {
        'strategies': strategy_names,
        'score_matrix': average_scores,
        'total_scores': strategy_total_scores,
        'rounds': rounds,
        'iterations': iterations
    }
    
    return results

def plot_tournament_results(results):
    """绘制锦标赛结果"""
    strategies = results['strategies']
    total_scores = results['total_scores']
    score_matrix = results['score_matrix']
    
    # 绘制总分柱状图
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    y_pos = np.arange(len(strategies))
    plt.barh(y_pos, total_scores, align='center')
    plt.yticks(y_pos, strategies)
    plt.xlabel('Total Score')
    plt.title('Strategy Tournament Results')
    
    # 绘制热力图
    plt.subplot(1, 2, 2)
    plt.imshow(score_matrix, cmap='hot')
    plt.colorbar(label='Average Score')
    plt.xticks(np.arange(len(strategies)), strategies, rotation=45)
    plt.yticks(np.arange(len(strategies)), strategies)
    plt.title('Pairwise Scores')
    
    plt.tight_layout()
    plt.savefig('tournament_results.png')
    plt.show()

def plot_learning_curve(q_strategy, opponents, rounds_list, iterations=5):
    """
    绘制Q-learning策略的学习曲线
    
    参数:
        q_strategy: Q-learning策略
        opponents: 对手策略列表
        rounds_list: 要测试的回合数列表
        iterations: 重复次数
    """
    plt.figure(figsize=(10, 6))
    
    for opponent in opponents:
        scores = []
        
        for rounds in rounds_list:
            iteration_scores = []
            for _ in range(iterations):
                # 重置策略
                q_strategy.history = []
                q_strategy.score = 0
                opponent.history = []
                opponent.score = 0
                
                q_score, _ = play_game(q_strategy, opponent, rounds)
                iteration_scores.append(q_score / rounds)  # 平均每回合得分
            
            # 计算平均
            scores.append(np.mean(iteration_scores))
        
        plt.plot(rounds_list, scores, marker='o', label=f'vs {opponent.name}')
    
    plt.xlabel('回合数')
    plt.ylabel('平均每回合得分')
    plt.title('Q-learning策略的学习曲线')
    plt.legend()
    plt.grid(True)
    plt.savefig('learning_curve.png')
    plt.show()

def main():
    # Configure matplotlib to support Chinese characters
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建所有策略
    strategies = [
        QLearningStrategy(exploration_rate=0.1),  # Q-learning策略
        AlwaysCooperate(),                        # 始终合作策略
        AlwaysDefect(),                           # 始终欺骗策略
        TitForTat(),                              # 一报还一报策略
        Random(),                                 # 随机策略
        GradualTFT()                              # 渐进式一报还一报策略
    ]
    
    # 进行锦标赛
    print("开始锦标赛...")
    results = tournament(strategies, rounds=200, iterations=10)
    
    # 保存结果
    save_results(results)
    
    # 绘制结果
    print("绘制锦标赛结果...")
    plot_tournament_results(results)
    
    # 绘制学习曲线
    print("绘制学习曲线...")
    q_strategy = QLearningStrategy(exploration_rate=0.2)  # 使用更高的探索率
    opponent_strategies = [
        AlwaysCooperate(),
        AlwaysDefect(),
        TitForTat()
    ]
    rounds_list = [10, 20, 50, 100, 200, 500, 1000]
    plot_learning_curve(q_strategy, opponent_strategies, rounds_list)
    
    print("测试完成!")

if __name__ == "__main__":
    main() 
