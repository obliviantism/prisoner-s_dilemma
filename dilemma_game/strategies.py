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
    }
]

# 策略实现函数
def execute_strategy(strategy_id, opponent_history):
    """
    执行指定的策略
    
    :param strategy_id: 策略ID
    :param opponent_history: 对手历史选择的列表
    :return: 策略的选择 ('C' 或 'D')
    """
    # 查找匹配的策略
    strategy = next((s for s in PRESET_STRATEGIES if s['id'] == strategy_id), None)
    
    if not strategy:
        # 未找到匹配策略，默认返回合作
        return 'C'
    
    # 准备执行环境
    import random
    safe_globals = {
        'random': random,
    }
    local_vars = {}
    
    # 执行策略代码
    try:
        exec(strategy['code'], safe_globals, local_vars)
        
        # 确保make_move函数存在
        if 'make_move' in local_vars and callable(local_vars['make_move']):
            # 调用make_move函数
            result = local_vars['make_move'](opponent_history)
            if result in ['C', 'D']:
                return result
    except Exception as e:
        print(f"执行策略 {strategy['name']} 时出错: {e}")
    
    # 失败时默认返回合作
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