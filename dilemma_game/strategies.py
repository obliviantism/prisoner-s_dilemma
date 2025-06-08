"""
预设策略定义模块

这个模块包含了囚徒困境游戏中所有预设策略的定义。
它作为系统中所有策略的单一真实来源。
"""

# 策略定义
# 包含名称、描述、代码和实现函数

PRESET_STRATEGIES = [
    {
        'id': 'always_cooperate',
        'name': '始终合作 (Always Cooperate)',
        'description': '无论对手采取什么行动，该策略都始终选择合作。',
        'code': '''def make_move(opponent_history):
    """
    始终合作策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    return 'C'
'''
    },
    {
        'id': 'always_defect',
        'name': '始终背叛 (Always Defect)',
        'description': '无论对手采取什么行动，该策略都始终选择背叛。',
        'code': '''def make_move(opponent_history):
    """
    始终背叛策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    return 'D'
'''
    },
    {
        'id': 'tit_for_tat',
        'name': '针锋相对 (Tit for Tat)',
        'description': '第一回合选择合作，随后模仿对手上一回合的选择。这是一种简单但非常有效的策略。',
        'code': '''def make_move(opponent_history):
    """
    针锋相对策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    if not opponent_history:  # 第一轮
        return 'C'  # 首轮选择合作
    
    # 模仿对手上一轮的选择
    return opponent_history[-1]
'''
    },
    {
        'id': 'suspicious_tit_for_tat',
        'name': '怀疑者 (Suspicious Tit for Tat)',
        'description': '第一回合选择背叛，随后模仿对手上一回合的选择。是针锋相对的一个变种。',
        'code': '''def make_move(opponent_history):
    """
    怀疑者策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    if not opponent_history:  # 第一轮
        return 'D'  # 首轮选择背叛
    
    # 模仿对手上一轮的选择
    return opponent_history[-1]
'''
    },
    {
        'id': 'random',
        'name': '随机策略 (Random)',
        'description': '随机选择合作或背叛，各50%的概率。',
        'code': '''import random

def make_move(opponent_history):
    """
    随机策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 随机返回 'C' 或 'D'，各50%的概率
    return random.choice(['C', 'D'])
'''
    },
    {
        'id': 'grudger',
        'name': '永不原谅 (Grudger)',
        'description': '开始时选择合作，但如果对手曾经背叛过，则永远选择背叛。',
        'code': '''def make_move(opponent_history):
    """
    永不原谅策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    if not opponent_history:  # 第一轮
        return 'C'  # 首轮选择合作
    
    # 如果对手曾经背叛过，永远选择背叛
    if 'D' in opponent_history:
        return 'D'
    return 'C'
'''
    },
    {
        'id': 'pavlov',
        'name': '胜者为王 (Pavlov)',
        'description': '如果上一回合双方选择相同（都合作或都背叛），则这一回合选择合作；否则选择背叛。',
        'code': '''def make_move(opponent_history):
    """
    胜者为王策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    if not opponent_history:  # 第一轮
        return 'C'  # 首轮选择合作
    
    # 简化版Pavlov策略实现
    # 第一轮默认合作，之后根据上一轮的结果决定
    if len(opponent_history) == 1:
        # 第二轮，根据对手第一轮是否合作决定
        return 'C' if opponent_history[0] == 'C' else 'D'
    
    # 从第三轮开始，实现真正的Pavlov逻辑
    # 假设我上一轮的选择与当前轮的选择相关
    # 如果上一轮我和对手选择相同，这一轮选择合作；否则选择背叛
    
    # 获取对手上上轮和上轮的选择
    prev_opponent_move = opponent_history[-1]  # 对手上一轮
    prev2_opponent_move = opponent_history[-2]  # 对手上上轮
    
    # 根据简化的Pavlov规则推断我上一轮的选择
    # 这是一个简化版，不是完全准确的Pavlov实现
    if len(opponent_history) == 2:
        my_prev_move = 'C' if opponent_history[0] == 'C' else 'D'
    else:
        # 如果上上轮我和对手选择相同，那么上一轮我应该选择合作
        # 否则上一轮我应该选择背叛
        if prev2_opponent_move == 'C':
            my_prev_move = 'C'  # 假设我上上轮选择合作
        else:
            my_prev_move = 'D'  # 假设我上上轮选择背叛
    
    # 应用Pavlov规则
    if my_prev_move == prev_opponent_move:
        return 'C'  # 如果上一轮双方选择相同，选择合作
    else:
        return 'D'  # 如果上一轮双方选择不同，选择背叛
'''
    },
    {
        'id': 'tit_for_two_tats',
        'name': '宽容版针锋相对 (Tit for Two Tats)',
        'description': '只有当对手连续两次背叛时才选择背叛，其他情况选择合作。比标准的针锋相对更宽容。',
        'code': '''def make_move(opponent_history):
    """
    宽容版针锋相对策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 只有当对手连续两次背叛才背叛，否则合作
    if len(opponent_history) >= 2 and opponent_history[-1] == 'D' and opponent_history[-2] == 'D':
        return 'D'
    return 'C'
'''
    },
    {
        'id': 'two_memory',
        'name': '两步记忆 (Two-Memory)',
        'description': '根据对手最近两次的选择来决定自己的策略，如果最近两次都是合作则选择合作，否则选择背叛。',
        'code': '''def make_move(opponent_history):
    """
    两步记忆策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 第一轮和第二轮选择合作
    if len(opponent_history) < 2:
        return 'C'
    
    # 如果对手最近两次选择都是合作，则合作
    if opponent_history[-1] == 'C' and opponent_history[-2] == 'C':
        return 'C'
    # 否则背叛
    return 'D'
'''
    },
    {
        'id': 'q_learning',
        'name': 'Q学习策略 (Q-Learning)',
        'description': '一种基于强化学习的自适应策略，通过与对手交互学习最优决策。该策略能够随着比赛的进行不断优化自己的行为。',
        'code': '''import random
import os
import pickle
import sys

def make_move(opponent_history, tournament_id=None):
    """
    基于Q-learning的强化学习策略
    
    :param opponent_history: 对手历史选择的列表
    :param tournament_id: 当前锦标赛ID，用于创建锦标赛特定的模型
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 获取当前状态字典
    state_dict = globals()
    
    # 当前锦标赛的模型键（使用tournament_id）
    model_key = f"ql_strategy_{tournament_id}" if tournament_id else "ql_strategy"
    history_key = f"last_history_length_{tournament_id}" if tournament_id else "last_history_length"
    
    # 初始化状态
    if model_key not in state_dict:
        # 参数设置
        learning_rate = 0.1
        discount_factor = 0.95
        exploration_rate = 0.1
        memory_length = 3
        
        # 工具函数定义
        def get_state(opponent_history, memory_length):
            """
            根据对手历史选择生成当前状态的字符串表示
            
            :param opponent_history: 对手的历史选择列表
            :param memory_length: 记忆长度
            :return: 代表当前状态的字符串
            """
            # 如果对手历史不足memory_length，用'N'（None）填充
            if len(opponent_history) < memory_length:
                padded_history = ['N'] * (memory_length - len(opponent_history)) + opponent_history
            else:
                # 只取最近的memory_length个选择
                padded_history = opponent_history[-memory_length:]
            
            # 生成状态字符串
            return ''.join(padded_history)
        
        def get_q_values(state, q_table):
            """
            获取指定状态的Q值。如果状态不存在，则初始化
            
            :param state: 状态字符串
            :param q_table: Q表
            :return: 状态对应的动作-值字典
            """
            if state not in q_table:
                # 初始化新状态的Q值
                q_table[state] = {
                    'C': 0.0,  # 合作的初始Q值
                    'D': 0.0   # 背叛的初始Q值
                }
            return q_table[state]
        
        def choose_action(state, q_table, exploration_rate):
            """
            根据当前状态选择动作（合作或背叛）
            使用ε-贪心策略平衡探索与利用
            
            :param state: 当前状态
            :param q_table: Q表
            :param exploration_rate: 探索率
            :return: 选择的动作: 'C'（合作）或'D'（背叛）
            """
            # 探索：以ε的概率随机选择动作
            if random.random() < exploration_rate:
                return random.choice(['C', 'D'])
            
            # 利用：选择Q值最高的动作
            q_values = get_q_values(state, q_table)
            
            # 如果两个动作的Q值相同，随机选择
            if q_values['C'] == q_values['D']:
                return random.choice(['C', 'D'])
            
            # 选择Q值最高的动作
            return 'C' if q_values['C'] > q_values['D'] else 'D'
        
        def update_q_value(state, action, reward, next_state, q_table, learning_rate, discount_factor):
            """
            更新Q表中的Q值
            使用Q-learning更新公式: Q(s,a) ← Q(s,a) + α[r + γ·max_a'Q(s',a') - Q(s,a)]
            
            :param state: 当前状态
            :param action: 执行的动作
            :param reward: 获得的奖励
            :param next_state: 执行动作后的新状态
            :param q_table: Q表
            :param learning_rate: 学习率
            :param discount_factor: 折扣因子
            """
            # 获取当前状态-动作的Q值
            q_values = get_q_values(state, q_table)
            current_q = q_values[action]
            
            # 获取下一状态的最大Q值
            next_q_values = get_q_values(next_state, q_table)
            max_next_q = max(next_q_values.values())
            
            # 计算新的Q值
            new_q = current_q + learning_rate * (reward + discount_factor * max_next_q - current_q)
            
            # 更新Q表
            q_table[state][action] = new_q
        
        def get_reward(my_choice, opponent_choice):
            """
            根据双方选择计算奖励
            
            :param my_choice: 我的选择
            :param opponent_choice: 对手的选择
            :return: 获得的奖励
            """
            reward_matrix = {
                ('C', 'C'): 3,  # 双方合作
                ('C', 'D'): 0,  # 我合作，对手背叛
                ('D', 'C'): 5,  # 我背叛，对手合作
                ('D', 'D'): 0   # 双方背叛
            }
            return reward_matrix[(my_choice, opponent_choice)]
        
        # 创建模型目录
        model_dir = os.path.join('models')
        os.makedirs(model_dir, exist_ok=True)
        
        # 如果有tournament_id，则为该锦标赛创建特定的模型文件
        if tournament_id:
            model_filename = f'q_learning_model_tournament_{tournament_id}.pkl'
        else:
            model_filename = 'q_learning_model.pkl'
        
        model_path = os.path.join(model_dir, model_filename)
        
        # 在状态字典中保存模型数据
        state_dict[model_key] = {
            'history': [],  # 存储(我的选择, 对手选择)的列表
            'q_table': {},  # 新的锦标赛从空的Q表开始
            'learning_rate': learning_rate,
            'discount_factor': discount_factor,
            'exploration_rate': exploration_rate,
            'memory_length': memory_length,
            'save_path': model_path,
            'round_counter': 0,  # 回合计数器，用于定期保存模型
            'get_state': get_state,
            'get_q_values': get_q_values,
            'choose_action': choose_action,
            'update_q_value': update_q_value,
            'get_reward': get_reward,
            'learning_curve': [],  # 学习曲线数据
            'tournament_id': tournament_id  # 存储锦标赛ID
        }
        state_dict[history_key] = 0
    
    # 当前模型的引用
    ql_strategy = state_dict[model_key]
    last_history_length = state_dict[history_key]
    
    # 更新上一轮对手选择
    if opponent_history and len(opponent_history) > last_history_length:
        if ql_strategy['history']:
            # 获取上一轮的状态
            last_state = ql_strategy['get_state'](opponent_history[:-1] if len(opponent_history) > 1 else [], ql_strategy['memory_length'])
            last_action = ql_strategy['history'][-1][0]
            opponent_action = opponent_history[-1]
            
            # 更新历史记录中对手的选择
            my_action, _ = ql_strategy['history'][-1]
            ql_strategy['history'][-1] = (my_action, opponent_action)
            
            # 计算奖励
            reward = ql_strategy['get_reward'](last_action, opponent_action)
            
            # 记录学习曲线数据点
            ql_strategy['learning_curve'].append(reward)
            
            # 获取当前状态
            current_state = ql_strategy['get_state'](opponent_history, ql_strategy['memory_length'])
            
            # 更新Q值
            ql_strategy['update_q_value'](last_state, last_action, reward, current_state, 
                           ql_strategy['q_table'], ql_strategy['learning_rate'], 
                           ql_strategy['discount_factor'])
            
            # 增加回合计数
            ql_strategy['round_counter'] += 1
            
            # 每50回合保存一次Q表和学习曲线
            if ql_strategy['round_counter'] % 50 == 0:
                try:
                    save_data = {
                        'q_table': ql_strategy['q_table'],
                        'learning_curve': ql_strategy['learning_curve'],
                        'tournament_id': tournament_id,
                        'history': ql_strategy['history']
                    }
                    
                    with open(ql_strategy['save_path'], 'wb') as f:
                        pickle.dump(save_data, f)
                    print(f"Q表和学习数据已保存到 {ql_strategy['save_path']}，包含{len(ql_strategy['q_table'])}个状态")
                except Exception as e:
                    print(f"保存Q表失败: {e}")
    
    # 记录当前历史长度
    state_dict[history_key] = len(opponent_history)
    
    # 获取当前状态
    current_state = ql_strategy['get_state'](opponent_history, ql_strategy['memory_length'])
    
    # 选择动作
    action = ql_strategy['choose_action'](current_state, ql_strategy['q_table'], ql_strategy['exploration_rate'])
    
    # 记录此次选择
    ql_strategy['history'].append((action, None))
    
    return action
'''
    },

    # 以下是Axelrod第一次锦标赛的其他策略

    {
        'id': 'davis',
        'name': 'Davis策略 (Davis)',
        'description': '类似针锋相对但有10%几率随机选择。',
        'code': '''import random

def make_move(opponent_history):
    """
    Davis策略 - 针锋相对但有随机因素
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 10%概率随机选择
    if random.random() < 0.1:
        return random.choice(['C', 'D'])
    
    # 第一轮选择合作
    if not opponent_history:
        return 'C'
    
    # 大部分时间模仿对手上一轮的选择
    return opponent_history[-1]
'''
    },

    {
        'id': 'joss',
        'name': 'Joss策略 (Joss)',
        'description': '类似针锋相对但有10%的几率随机背叛。',
        'code': '''import random

def make_move(opponent_history):
    """
    Joss策略 - 针锋相对但有10%几率背叛
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 10%的几率随机背叛
    if random.random() < 0.1:
        return 'D'
    
    # 第一轮选择合作
    if not opponent_history:
        return 'C'
    
    # 其他情况下模仿对手上一轮的选择
    return opponent_history[-1]
'''
    },

    {
        'id': 'tullock',
        'name': 'Tullock策略 (Tullock)',
        'description': '一个简单的周期性策略。前11轮合作，之后如果对手有背叛就背叛，否则继续合作。',
        'code': '''def make_move(opponent_history):
    """
    Tullock策略 - 简单的周期性策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 前11轮合作
    if len(opponent_history) < 11:
        return 'C'
    
    # 之后，如果对手有背叛，则背叛；否则合作
    if 'D' in opponent_history:
        return 'D'
    else:
        return 'C'
'''
    },

    {
        'id': 'nydegger',
        'name': 'Nydegger策略 (Nydegger)',
        'description': '基于前三轮历史制定决策的复杂策略。',
        'code': '''def make_move(opponent_history):
    """
    Nydegger策略 - 基于前三轮历史的复杂决策
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 前三轮的特定模式
    if not opponent_history:
        return 'C'  # 第一轮合作
    elif len(opponent_history) == 1:
        return 'D'  # 第二轮背叛
    elif len(opponent_history) == 2:
        if opponent_history[0] == 'D':
            return 'D'  # 如果对手第一轮背叛，第三轮背叛
        else:
            return 'C'  # 如果对手第一轮合作，第三轮合作
    
    # 第四轮开始使用基于历史的复杂规则
    # 检查前三轮对手选择，计算一个状态索引
    history_index = 0
    if opponent_history[-3] == 'D':
        history_index += 4
    if opponent_history[-2] == 'D':
        history_index += 2
    if opponent_history[-1] == 'D':
        history_index += 1
    
    # 基于历史状态索引决定行动
    if history_index in [0, 2, 4, 6]:  # 对应状态 CCC, CDC, DCC, DDC
        return 'C'
    else:  # 对应状态 CCD, CDD, DCD, DDD
        return 'D'
'''
    },

    {
        'id': 'grofman',
        'name': 'Grofman策略 (Grofman)',
        'description': '基于合作/背叛比例的概率策略。',
        'code': '''import random

def make_move(opponent_history):
    """
    Grofman策略 - 基于合作/背叛比例的概率决策
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 前两轮合作
    if len(opponent_history) < 2:
        return 'C'
    
    # 计算对手合作的比例
    cooperation_ratio = opponent_history.count('C') / len(opponent_history)
    
    # 如果对手合作比例高于70%，则合作；否则根据对手的合作比例决定
    if cooperation_ratio > 0.7:
        return 'C'
    elif random.random() < cooperation_ratio:
        return 'C'
    else:
        return 'D'
'''
    },

    {
        'id': 'shubik',
        'name': 'Shubik策略 (Shubik)',
        'description': '一个复杂的报复策略，对方每背叛一次，就连续背叛n次作为惩罚。',
        'code': '''def make_move(opponent_history):
    """
    Shubik策略 - 复杂的报复策略
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 获取当前状态
    state_dict = globals()
    
    # 策略状态初始化
    if 'shubik_state' not in state_dict:
        state_dict['shubik_state'] = {
            'retaliation_count': 0,  # 当前需要进行的报复次数
            'betrayals': 0,  # 对手背叛的次数
        }
    
    # 第一轮合作
    if not opponent_history:
        return 'C'
    
    # 检查对手上一轮是否背叛
    if opponent_history[-1] == 'D':
        state_dict['shubik_state']['betrayals'] += 1
        # 新的背叛触发更长时间的报复
        state_dict['shubik_state']['retaliation_count'] = state_dict['shubik_state']['betrayals']
    
    # 如果还在报复阶段
    if state_dict['shubik_state']['retaliation_count'] > 0:
        state_dict['shubik_state']['retaliation_count'] -= 1
        return 'D'
    
    # 默认合作
    return 'C'
'''
    },

    {
        'id': 'stein_and_rapoport',
        'name': 'Stein & Rapoport策略 (S&R)',
        'description': '类似针锋相对但有探测系统。前四轮CDCD，之后如果检测到对方模仿，则利用。',
        'code': '''def make_move(opponent_history):
    """
    Stein & Rapoport策略 - 带探测系统的针锋相对变体
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 获取当前状态
    state_dict = globals()
    
    # 前四轮按照特定模式行动: CDCD
    if len(opponent_history) < 4:
        return 'C' if len(opponent_history) % 2 == 0 else 'D'
    
    # 检查对手是否是针锋相对策略
    if len(opponent_history) == 4:
        is_tit_for_tat = (
            opponent_history[1] == 'C' and 
            opponent_history[2] == 'D' and 
            opponent_history[3] == 'C'
        )
        
        # 存储检测结果
        state_dict['sr_state'] = {'is_opponent_tft': is_tit_for_tat}
    
    # 如果检测到对手是针锋相对，在最后轮背叛以获得额外收益
    if 'sr_state' in state_dict and state_dict['sr_state'].get('is_opponent_tft', False):
        return 'D'  # 利用针锋相对策略
    
    # 默认使用针锋相对策略
    return opponent_history[-1]
'''
    },

    {
        'id': 'downing',
        'name': 'Downing策略 (Downing)',
        'description': '尝试建立对手行为模型的策略。开始时背叛，然后根据对手的响应模式调整策略。',
        'code': '''def make_move(opponent_history):
    """
    Downing策略 - 尝试建立对手模型
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 获取状态
    state_dict = globals()
    
    # 初始化状态
    if 'downing_state' not in state_dict:
        state_dict['downing_state'] = {
            'cooperation_after_c': 0,  # 对手在我合作后的合作次数
            'cooperation_after_d': 0,  # 对手在我背叛后的合作次数
            'defection_after_c': 0,    # 对手在我合作后的背叛次数
            'defection_after_d': 0,    # 对手在我背叛后的背叛次数
            'my_last_move': None       # 我上一轮的选择
        }
    
    # 前两轮背叛以收集信息
    if len(opponent_history) < 2:
        state_dict['downing_state']['my_last_move'] = 'D'
        return 'D'
    
    # 更新对手行为统计
    if len(opponent_history) >= 2:
        last_opponent_move = opponent_history[-1]
        if state_dict['downing_state']['my_last_move'] == 'C':
            if last_opponent_move == 'C':
                state_dict['downing_state']['cooperation_after_c'] += 1
            else:
                state_dict['downing_state']['defection_after_c'] += 1
        else:  # 我上一轮背叛
            if last_opponent_move == 'C':
                state_dict['downing_state']['cooperation_after_d'] += 1
            else:
                state_dict['downing_state']['defection_after_d'] += 1
    
    # 计算对手行为概率
    p_cooperate_after_c = state_dict['downing_state']['cooperation_after_c'] / max(1, state_dict['downing_state']['cooperation_after_c'] + state_dict['downing_state']['defection_after_c'])
    p_cooperate_after_d = state_dict['downing_state']['cooperation_after_d'] / max(1, state_dict['downing_state']['cooperation_after_d'] + state_dict['downing_state']['defection_after_d'])
    
    # 根据概率决定行动
    if p_cooperate_after_c >= p_cooperate_after_d:
        # 如果对手在我合作后更可能合作，则选择合作
        state_dict['downing_state']['my_last_move'] = 'C'
        return 'C'
    else:
        # 如果对手在我背叛后更可能合作，则选择背叛
        state_dict['downing_state']['my_last_move'] = 'D'
        return 'D'
'''
    },

    {
        'id': 'graaskamp',
        'name': 'Graaskamp策略 (Graaskamp)',
        'description': '一个复杂的模式检测系统，尝试找出对手的周期性行为。由James Graaskamp设计，在Axelrod第一次锦标赛中使用。',
        'code': '''def make_move(opponent_history):
    """
    Graaskamp策略 - 模式检测系统
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 初始几轮的特定模式
    if len(opponent_history) < 10:
        if len(opponent_history) % 2 == 0:
            return 'C'  # 偶数轮合作
        else:
            return 'D'  # 奇数轮背叛
    
    # 尝试检测对手是否有周期性模式
    # 检查对手最近的行为是否有2-4轮的周期
    for period in range(2, 5):
        if len(opponent_history) >= 2 * period:
            is_periodic = True
            for i in range(period):
                if opponent_history[-(i+1)] != opponent_history[-(i+1+period)]:
                    is_periodic = False
                    break
            
            if is_periodic:
                # 如果检测到周期，预测下一步并做出反应
                # 假设对手会重复周期性行为
                next_expected = opponent_history[-period]
                if next_expected == 'C':
                    return 'D'  # 如果预期对手会合作，则背叛以获得更高收益
                else:
                    return 'C'  # 如果预期对手会背叛，则合作以减少损失
    
    # 如果没有检测到明确模式，使用针锋相对
    return opponent_history[-1]
'''
    },

    {
        'id': 'tideman_and_chieruzzi',
        'name': 'Tideman & Chieruzzi策略 (T&C)',
        'description': '一个检测对手周期性模式的策略，针对不同对手类型采用不同应对策略。由Nicolaus Tideman & Paula Chieruzzi设计，在Axelrod第一次锦标赛中使用。',
        'code': '''def make_move(opponent_history):
    """
    Tideman & Chieruzzi策略 - 检测对手周期性模式
    
    :param opponent_history: 对手历史选择的列表
    :return: 'C' 表示合作，'D' 表示背叛
    """
    # 获取当前状态
    state_dict = globals()
    
    # 初始行为
    if not opponent_history:
        return 'C'  # 第一轮合作
    
    # 计算对手背叛的总次数
    defections = opponent_history.count('D')
    
    # 如果对手从未背叛，则始终合作
    if defections == 0:
        return 'C'
    
    # 如果背叛率超过40%，则切换到惩罚模式
    if defections / len(opponent_history) > 0.4:
        # 每检测到8次背叛，进行一次长期惩罚
        if defections % 8 == 0:
            # 全局状态跟踪惩罚周期
            if 'tc_state' not in state_dict:
                state_dict['tc_state'] = {'punishment_active': False, 'punishment_left': 0}
            
            # 启动惩罚
            state_dict['tc_state']['punishment_active'] = True
            state_dict['tc_state']['punishment_left'] = 5  # 连续惩罚5轮
    
    # 处理惩罚模式
    if 'tc_state' in state_dict and state_dict['tc_state']['punishment_active']:
        if state_dict['tc_state']['punishment_left'] > 0:
            state_dict['tc_state']['punishment_left'] -= 1
            return 'D'  # 执行惩罚
        else:
            state_dict['tc_state']['punishment_active'] = False
    
    # 默认使用针锋相对策略
    return opponent_history[-1]
'''
    }
]

# 策略实现函数
def execute_strategy(strategy_id, opponent_history, **kwargs):
    """
    执行指定的策略
    
    :param strategy_id: 策略ID
    :param opponent_history: 对手历史选择的列表
    :param kwargs: 额外的参数，如tournament_id
    :return: 策略的选择 ('C' 或 'D')
    """
    # 查找匹配的策略
    strategy = next((s for s in PRESET_STRATEGIES if s['id'] == strategy_id), None)
    
    if not strategy:
        # 未找到匹配策略，记录错误
        print(f"策略 {strategy_id} 未找到，默认返回合作")
        return 'C'
    
    # 创建一个持久的全局状态对象，用于保存策略状态
    # 使用字典，键为策略ID
    if 'STRATEGY_STATES' not in globals():
        globals()['STRATEGY_STATES'] = {}
    
    # 获取或创建该策略的状态
    strategy_key = f"{strategy_id}"
    if 'tournament_id' in kwargs and kwargs['tournament_id']:
        strategy_key = f"{strategy_id}_{kwargs['tournament_id']}"
    
    if strategy_key not in globals()['STRATEGY_STATES']:
        globals()['STRATEGY_STATES'][strategy_key] = {}
    
    # 准备执行环境
    import random
    import os
    import pickle
    import sys
    import inspect
    
    # 创建安全的执行环境，但允许访问持久状态
    safe_globals = {
        'random': random,
        'os': os,
        'pickle': pickle,
        'sys': sys,
        'inspect': inspect,
        'globals': lambda: globals()['STRATEGY_STATES'][strategy_key],  # 替换全局函数以返回策略特定状态
        'print': print  # 允许打印调试信息
    }
    local_vars = {}
    
    # 执行策略代码
    try:
        exec(strategy['code'], safe_globals, local_vars)
        
        # 确保make_move函数存在
        if 'make_move' in local_vars and callable(local_vars['make_move']):
            # 判断make_move函数是否接受额外参数
            sig = inspect.signature(local_vars['make_move'])
            
            if len(sig.parameters) > 1 and 'tournament_id' in kwargs:
                # Q-learning策略，传递tournament_id
                result = local_vars['make_move'](opponent_history, tournament_id=kwargs.get('tournament_id'))
            else:
                # 标准策略，只传递opponent_history
                result = local_vars['make_move'](opponent_history)
                
            if result in ['C', 'D']:
                return result
            else:
                print(f"策略 {strategy_id} 返回无效结果: {result}，应为 'C' 或 'D'")
    except Exception as e:
        print(f"执行策略时出错 ({strategy_id}): {e}")
        import traceback
        traceback.print_exc()  # 打印完整的错误堆栈
        
        # 根据策略类型提供合理的默认行为
        if strategy_id == 'always_defect':
            return 'D'
        elif strategy_id == 'random':
            return random.choice(['C', 'D'])
        elif strategy_id == 'tit_for_tat':
            return 'C' if not opponent_history else opponent_history[-1]
    
    # 如果到这里还没有返回有效结果，默认返回合作
    print(f"策略 {strategy_id} 执行失败，默认返回合作")
    return 'C'

def get_all_strategies():
    """
    获取所有预设策略
    
    :return: 策略列表
    """
    return PRESET_STRATEGIES

def get_strategy_by_id(strategy_id):
    """
    根据ID获取策略
    
    :param strategy_id: 策略ID
    :return: 策略对象，如果未找到则返回None
    """
    return next((s for s in PRESET_STRATEGIES if s['id'] == strategy_id), None) 