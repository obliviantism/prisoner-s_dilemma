"""
囚徒困境的Q-learning强化学习算法策略实现

通过学习动作-状态值（Q值）来优化决策
"""

import random
import pickle
import os
from typing import List, Dict, Tuple, Union

class QLearningStrategy:
    """
    基于Q-learning的强化学习策略。
    此策略会学习适应对手的行为模式并做出最优决策。
    """
    
    def __init__(self, name: str = "Q-Learning Strategy", 
                 learning_rate: float = 0.1, 
                 discount_factor: float = 0.95, 
                 exploration_rate: float = 0.1,
                 memory_length: int = 3,
                 save_path: str = None):
        """
        初始化Q-learning策略。
        
        参数:
            name: 策略名称
            learning_rate: 学习率，控制Q值更新的速度
            discount_factor: 折扣因子，控制未来奖励的重要性
            exploration_rate: 探索率，控制随机探索的概率
            memory_length: 记忆长度，使用多少个历史回合来表示状态
            save_path: Q表保存路径
        """
        self.name = name
        self.learning_rate = learning_rate  # α (alpha)
        self.discount_factor = discount_factor  # γ (gamma)
        self.exploration_rate = exploration_rate  # ε (epsilon)
        self.memory_length = memory_length
        self.save_path = save_path
        
        # Q表: 将状态-动作对映射到Q值
        self.q_table: Dict[str, Dict[str, float]] = {}
        
        # 历史记录
        self.history: List[Tuple[str, str]] = []  # (我的选择，对手的选择)
        self.score = 0
        
        # 尝试加载已有的Q表
        if save_path and os.path.exists(save_path):
            try:
                with open(save_path, 'rb') as f:
                    self.q_table = pickle.load(f)
                print(f"已加载Q表，包含{len(self.q_table)}个状态")
            except Exception as e:
                print(f"加载Q表失败: {e}")
    
    def get_state(self, opponent_history: List[str]) -> str:
        """
        根据对手历史选择生成当前状态的字符串表示。
        
        参数:
            opponent_history: 对手的历史选择列表
            
        返回:
            代表当前状态的字符串
        """
        # 如果对手历史不足memory_length，用'N'（None）填充
        if len(opponent_history) < self.memory_length:
            padded_history = ['N'] * (self.memory_length - len(opponent_history)) + opponent_history
        else:
            # 只取最近的memory_length个选择
            padded_history = opponent_history[-self.memory_length:]
        
        # 生成状态字符串
        return ''.join(padded_history)
    
    def get_q_values(self, state: str) -> Dict[str, float]:
        """
        获取指定状态的Q值。如果状态不存在，则初始化。
        
        参数:
            state: 状态字符串
            
        返回:
            状态对应的动作-值字典
        """
        if state not in self.q_table:
            # 初始化新状态的Q值
            self.q_table[state] = {
                'C': 0.0,  # 合作的初始Q值
                'D': 0.0   # 欺骗的初始Q值
            }
        return self.q_table[state]
    
    def choose_action(self, state: str) -> str:
        """
        根据当前状态选择动作（合作或欺骗）。
        使用ε-贪心策略平衡探索与利用。
        
        参数:
            state: 当前状态
            
        返回:
            选择的动作: 'C'（合作）或'D'（欺骗）
        """
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
    
    def update_q_value(self, state: str, action: str, reward: float, next_state: str):
        """
        更新Q表中的Q值。
        使用Q-learning更新公式: Q(s,a) ← Q(s,a) + α[r + γ·max_a'Q(s',a') - Q(s,a)]
        
        参数:
            state: 当前状态
            action: 执行的动作
            reward: 获得的奖励
            next_state: 执行动作后的新状态
        """
        # 获取当前状态-动作的Q值
        q_values = self.get_q_values(state)
        current_q = q_values[action]
        
        # 获取下一状态的最大Q值
        next_q_values = self.get_q_values(next_state)
        max_next_q = max(next_q_values.values())
        
        # 计算新的Q值
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        
        # 更新Q表
        self.q_table[state][action] = new_q
    
    def get_reward(self, my_choice: str, opponent_choice: str) -> float:
        """
        根据双方选择计算奖励。
        
        参数:
            my_choice: 我的选择
            opponent_choice: 对手的选择
            
        返回:
            获得的奖励
        """
        reward_matrix = {
            ('C', 'C'): 3,  # 双方合作
            ('C', 'D'): 0,  # 我合作，对手欺骗
            ('D', 'C'): 5,  # 我欺骗，对手合作
            ('D', 'D'): 0   # 双方欺骗
        }
        return reward_matrix[(my_choice, opponent_choice)]
    
    def make_move(self, opponent_history: List[str]) -> str:
        """
        根据对手历史选择下一步动作。
        如果是首次调用，将执行一个标准的合作动作。
        
        参数:
            opponent_history: 对手的历史选择列表
            
        返回:
            'C'表示合作，'D'表示欺骗
        """
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
            
            # 更新Q值
            self.update_q_value(last_state, last_action, reward, current_state)
        
        # 记录此次选择（等对手行动后再更新对手的选择）
        self.history.append((action, None))
        
        return action
    
    def update_opponent_action(self, opponent_action: str):
        """
        更新最后一个回合中对手的选择。
        
        参数:
            opponent_action: 对手的选择
        """
        if self.history:
            # 更新最后一个历史记录中对手的选择
            my_action, _ = self.history[-1]
            self.history[-1] = (my_action, opponent_action)
            
            # 更新累计得分
            reward = self.get_reward(my_action, opponent_action)
            self.score += reward
    
    def save_q_table(self):
        """保存Q表到文件"""
        if self.save_path:
            try:
                with open(self.save_path, 'wb') as f:
                    pickle.dump(self.q_table, f)
                print(f"Q表已保存，包含{len(self.q_table)}个状态")
            except Exception as e:
                print(f"保存Q表失败: {e}")

# 符合项目需求的make_move函数
def make_move(opponent_history):
    """
    外部调用的函数，用于和现有系统集成。
    
    参数:
        opponent_history: 对手的历史选择列表
    
    返回:
        'C'表示合作，'D'表示欺骗
    """
    # 获取或创建全局QLearningStrategy实例
    global ql_strategy
    if 'ql_strategy' not in globals():
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, 'q_learning_model.pkl')
        ql_strategy = QLearningStrategy(save_path=save_path)
    
    # 更新上一轮对手选择
    if opponent_history and 'last_history_length' in globals():
        new_opponent_action = opponent_history[-1]
        ql_strategy.update_opponent_action(new_opponent_action)
    
    # 记录当前历史长度
    global last_history_length
    last_history_length = len(opponent_history)
    
    # 做出决策
    action = ql_strategy.make_move(opponent_history)
    
    # 定期保存模型
    if len(ql_strategy.history) % 50 == 0:
        ql_strategy.save_q_table()
    
    return action

# 测试代码
if __name__ == "__main__":
    # 创建Q-learning策略
    ql = QLearningStrategy()
    
    # 模拟对手：总是背叛
    always_defect_history = []
    for _ in range(100):
        # Q-learning策略选择动作
        ql_action = ql.make_move(always_defect_history)
        
        # 对手总是选择背叛
        opponent_action = 'D'
        
        # 更新对手的选择
        ql.update_opponent_action(opponent_action)
        
        # 记录对手历史
        always_defect_history.append(opponent_action)
        
        print(f"回合 {_+1}: Q-learning选择 {ql_action}, 对手选择 {opponent_action}")
    
    print(f"最终得分: {ql.score}")
    
    # 打印部分Q表
    print("\n部分Q表:")
    count = 0
    for state, actions in ql.q_table.items():
        print(f"状态 {state}: {actions}")
        count += 1
        if count >= 10:  # 只显示前10个状态
            break 