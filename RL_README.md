# 囚徒困境中的强化学习策略

本项目实现了一个基于Q-learning的强化学习算法，用于解决囚徒困境(Prisoner's Dilemma)问题。强化学习是一种机器学习方法，通过与环境交互并从反馈中学习，使智能体在没有明确指导的情况下学会做出最优决策。

## 囚徒困境简介

囚徒困境是博弈论中的一个经典问题，两名囚犯可以选择合作或背叛。支付矩阵如下：

- 双方合作：各获得3分
- 一方合作，一方背叛：背叛者获得5分，合作者获得0分
- 双方背叛：各获得0分

虽然双方都合作是总体最优解，但从个体角度看，无论对方选择什么，背叛总是比合作有更高的收益。这导致理性自利的个体倾向于选择背叛，最终得到次优结果。这种"理性导致非理性结果"的悖论是囚徒困境的核心。

## Q-learning算法原理

Q-learning是一种基于值函数的无模型强化学习算法，特别适合于解决序列决策问题。Q-learning的核心思想是学习一个状态-动作值函数（Q函数），表示在某状态下采取某动作的长期价值。

### 核心公式

Q-learning使用以下公式更新Q值：

```
Q(s,a) ← Q(s,a) + α[r + γ·max_a'Q(s',a') - Q(s,a)]
```

其中：
- Q(s,a)：状态s下采取动作a的Q值
- α：学习率，控制更新速度
- r：即时奖励
- γ：折扣因子，决定未来奖励的重要性
- max_a'Q(s',a')：下一状态s'的最大Q值
- [r + γ·max_a'Q(s',a') - Q(s,a)]：时序差分误差，表示估计值与实际值的差异

### 在囚徒困境中的应用

在囚徒困境中，我们的Q-learning策略的工作方式如下：

1. **状态表示**：使用对手最近几轮的选择来表示状态
2. **动作选择**：在每个状态下选择合作(C)或背叛(D)
3. **奖励机制**：根据双方选择和支付矩阵获得对应分数作为奖励
4. **学习过程**：通过Q-learning公式更新Q表中的值
5. **探索与利用**：使用ε-贪心策略平衡探索新策略与利用已知最优策略

## 项目文件说明

- `rl_strategy.py`：Q-learning强化学习策略的核心实现
- `test_rl_strategy.py`：测试脚本，用于评估策略性能和与其他经典策略对比
- `RL_README.md`：本文档，提供算法原理和使用说明

## 核心类和函数

### QLearningStrategy 类

这是核心的Q-learning策略实现类，主要包括：

- `__init__`：初始化Q-learning策略，设置各种参数
- `get_state`：根据对手历史选择生成当前状态
- `get_q_values`：获取指定状态的Q值
- `choose_action`：使用ε-贪心策略选择动作
- `update_q_value`：更新Q表中的Q值
- `make_move`：根据对手历史选择下一步动作
- `update_opponent_action`：更新对手选择和得分
- `save_q_table`：保存Q表到文件

### make_move 函数

这是与现有系统集成的接口函数，符合项目要求的格式。它：

1. 创建或获取全局QLearningStrategy实例
2. 更新对手上一轮的选择
3. 做出当前轮的决策
4. 定期保存学习的模型

## 测试与评估

`test_rl_strategy.py`提供了全面的测试框架：

1. **锦标赛评估**：将Q-learning策略与其他经典策略（如永远合作、永远背叛、一报还一报等）进行对比
2. **学习曲线**：评估Q-learning策略在不同回合数下的学习效果
3. **可视化**：生成图表展示各策略性能对比和Q-learning学习过程

## 如何使用

1. 在Django项目的Strategy模型中添加以下代码作为策略代码：

```python
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
```

2. 运行测试脚本评估策略性能：

```bash
python test_rl_strategy.py
```

## 实验结果和讨论

Q-learning策略表现出以下特点：

1. **适应性**：能够学习并适应不同对手的行为模式
2. **长期优化**：随着对弈回合的增加，性能逐渐提升
3. **均衡性能**：在面对各种对手时，都能取得相对稳定的成绩

与其他经典策略相比，Q-learning策略的优势在于：

- 相比永远合作：更能防御利用型策略
- 相比永远背叛：能够与合作型策略建立互利关系
- 相比一报还一报：能够从错误中恢复，更加灵活

## 进一步改进方向

1. **更复杂的状态表示**：考虑更多历史信息或模式
2. **深度Q网络(DQN)**：使用神经网络代替Q表，处理更大的状态空间
3. **多智能体强化学习**：考虑多个智能体同时学习的情况
4. **上下文感知学习**：识别对手策略类型并采取针对性应对 