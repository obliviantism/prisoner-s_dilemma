"""
简化版Q-learning策略，专为囚徒困境Django项目设计
该代码可以作为一个策略直接粘贴到Django项目的策略库中
"""

def make_move(history):
    """
    根据对手历史选择做出决策
    
    参数:
        history: 对手的历史选择列表
    
    返回:
        'C'表示合作，'D'表示背叛
    """
    # 初始化全局变量
    global ql_strategy, last_history_length
    if 'ql_strategy' not in globals():
        # 导入所需模块
        import random
        
        # 创建Q表字典
        q_table = {}
        
        # 参数设置
        learning_rate = 0.1
        discount_factor = 0.95
        exploration_rate = 0.1
        memory_length = 3
        
        # 方法定义(仅在第一次调用时执行)
        def get_state(opponent_history):
            # 如果对手历史不足memory_length，用'N'填充
            if len(opponent_history) < memory_length:
                padded_history = ['N'] * (memory_length - len(opponent_history)) + opponent_history
            else:
                # 只取最近的memory_length个选择
                padded_history = opponent_history[-memory_length:]
            return ''.join(padded_history)
        
        def get_q_values(state):
            if state not in q_table:
                q_table[state] = {'C': 0.0, 'D': 0.0}
            return q_table[state]
        
        def choose_action(state):
            # 探索：以exploration_rate的概率随机选择
            if random.random() < exploration_rate:
                return random.choice(['C', 'D'])
            
            # 利用：选择Q值最高的动作
            q_values = get_q_values(state)
            if q_values['C'] == q_values['D']:
                return random.choice(['C', 'D'])
            return 'C' if q_values['C'] > q_values['D'] else 'D'
        
        def get_reward(my_choice, opponent_choice):
            reward_matrix = {
                ('C', 'C'): 3,  # 双方合作
                ('C', 'D'): 0,  # 我合作，对手背叛
                ('D', 'C'): 5,  # 我背叛，对手合作
                ('D', 'D'): 0   # 双方背叛
            }
            return reward_matrix[(my_choice, opponent_choice)]
        
        def update_q_value(state, action, reward, next_state):
            q_values = get_q_values(state)
            current_q = q_values[action]
            
            next_q_values = get_q_values(next_state)
            max_next_q = max(next_q_values.values())
            
            new_q = current_q + learning_rate * (reward + discount_factor * max_next_q - current_q)
            q_table[state][action] = new_q
        
        # 全局变量定义
        ql_strategy = {
            'history': [],  # 存储(我的选择, 对手选择)的列表
            'get_state': get_state,
            'get_q_values': get_q_values,
            'choose_action': choose_action,
            'get_reward': get_reward,
            'update_q_value': update_q_value
        }
        last_history_length = 0
    
    # 更新上一轮对手选择
    if history and len(history) > last_history_length:
        if ql_strategy['history']:
            last_state = ql_strategy['get_state'](history[:-1] if len(history) > 1 else [])
            last_action = ql_strategy['history'][-1][0]
            opponent_action = history[-1]
            
            # 更新历史记录中对手的选择
            my_action, _ = ql_strategy['history'][-1]
            ql_strategy['history'][-1] = (my_action, opponent_action)
            
            # 计算奖励并更新Q值
            reward = ql_strategy['get_reward'](last_action, opponent_action)
            current_state = ql_strategy['get_state'](history)
            ql_strategy['update_q_value'](last_state, last_action, reward, current_state)
    
    # 记录当前历史长度
    last_history_length = len(history)
    
    # 获取当前状态
    current_state = ql_strategy['get_state'](history)
    
    # 选择动作
    action = ql_strategy['choose_action'](current_state)
    
    # 记录此次选择
    ql_strategy['history'].append((action, None))
    
    return action

# 以下是Django项目中使用的示例代码
"""
from django.db import models
from django.contrib.auth.models import User

# 创建Q-learning策略
ql_strategy = Strategy(
    name="Q-Learning Strategy",
    description="基于Q-learning的强化学习策略，能够通过经验学习适应对手行为模式",
    code='''
def make_move(history):
    # 初始化全局变量
    global ql_strategy, last_history_length
    if 'ql_strategy' not in globals():
        # 导入所需模块
        import random
        
        # 创建Q表字典
        q_table = {}
        
        # 参数设置
        learning_rate = 0.1
        discount_factor = 0.95
        exploration_rate = 0.1
        memory_length = 3
        
        # 方法定义(仅在第一次调用时执行)
        def get_state(opponent_history):
            # 如果对手历史不足memory_length，用'N'填充
            if len(opponent_history) < memory_length:
                padded_history = ['N'] * (memory_length - len(opponent_history)) + opponent_history
            else:
                # 只取最近的memory_length个选择
                padded_history = opponent_history[-memory_length:]
            return ''.join(padded_history)
        
        def get_q_values(state):
            if state not in q_table:
                q_table[state] = {'C': 0.0, 'D': 0.0}
            return q_table[state]
        
        def choose_action(state):
            # 探索：以exploration_rate的概率随机选择
            if random.random() < exploration_rate:
                return random.choice(['C', 'D'])
            
            # 利用：选择Q值最高的动作
            q_values = get_q_values(state)
            if q_values['C'] == q_values['D']:
                return random.choice(['C', 'D'])
            return 'C' if q_values['C'] > q_values['D'] else 'D'
        
        def get_reward(my_choice, opponent_choice):
            reward_matrix = {
                ('C', 'C'): 3,  # 双方合作
                ('C', 'D'): 0,  # 我合作，对手背叛
                ('D', 'C'): 5,  # 我背叛，对手合作
                ('D', 'D'): 0   # 双方背叛
            }
            return reward_matrix[(my_choice, opponent_choice)]
        
        def update_q_value(state, action, reward, next_state):
            q_values = get_q_values(state)
            current_q = q_values[action]
            
            next_q_values = get_q_values(next_state)
            max_next_q = max(next_q_values.values())
            
            new_q = current_q + learning_rate * (reward + discount_factor * max_next_q - current_q)
            q_table[state][action] = new_q
        
        # 全局变量定义
        ql_strategy = {
            'history': [],  # 存储(我的选择, 对手选择)的列表
            'get_state': get_state,
            'get_q_values': get_q_values,
            'choose_action': choose_action,
            'get_reward': get_reward,
            'update_q_value': update_q_value
        }
        last_history_length = 0
    
    # 更新上一轮对手选择
    if history and len(history) > last_history_length:
        if ql_strategy['history']:
            last_state = ql_strategy['get_state'](history[:-1] if len(history) > 1 else [])
            last_action = ql_strategy['history'][-1][0]
            opponent_action = history[-1]
            
            # 更新历史记录中对手的选择
            my_action, _ = ql_strategy['history'][-1]
            ql_strategy['history'][-1] = (my_action, opponent_action)
            
            # 计算奖励并更新Q值
            reward = ql_strategy['get_reward'](last_action, opponent_action)
            current_state = ql_strategy['get_state'](history)
            ql_strategy['update_q_value'](last_state, last_action, reward, current_state)
    
    # 记录当前历史长度
    last_history_length = len(history)
    
    # 获取当前状态
    current_state = ql_strategy['get_state'](history)
    
    # 选择动作
    action = ql_strategy['choose_action'](current_state)
    
    # 记录此次选择
    ql_strategy['history'].append((action, None))
    
    return action
''',
    created_by=user
)
ql_strategy.save()
print(f"已创建 Q-Learning 策略")
""" 