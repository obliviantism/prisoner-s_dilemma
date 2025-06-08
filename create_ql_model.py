"""
创建简单的Q-learning模型文件
"""

import os
import pickle

def create_q_learning_model():
    """
    创建一个简单的Q-learning模型文件，包含基本的Q值表
    """
    # 创建models目录
    model_dir = 'models'
    os.makedirs(model_dir, exist_ok=True)
    
    # 模型文件路径
    model_path = os.path.join(model_dir, 'q_learning_model.pkl')
    
    # 创建一个简单的Q值表
    q_table = {
        'CCC': {'C': 3.0, 'D': 5.0},  # 对手连续合作3次
        'CCD': {'C': 1.5, 'D': 3.0},  # 对手合作后突然背叛
        'CDC': {'C': 2.0, 'D': 4.0},  # 对手合作背叛交替
        'CDD': {'C': 0.5, 'D': 2.0},  # 对手连续背叛
        'DCC': {'C': 3.5, 'D': 4.0},  # 对手背叛后连续合作
        'DCD': {'C': 1.0, 'D': 2.5},  # 对手背叛合作交替
        'DDC': {'C': 2.0, 'D': 3.5},  # 对手连续背叛后合作
        'DDD': {'C': 0.0, 'D': 1.5},  # 对手连续背叛
        'NNN': {'C': 2.0, 'D': 2.0},  # 初始状态，无历史
        'NNC': {'C': 3.0, 'D': 4.0},  # 只有一次历史，对手合作
        'NND': {'C': 1.0, 'D': 2.0},  # 只有一次历史，对手背叛
        'NCC': {'C': 3.2, 'D': 4.5},  # 两次历史，对手连续合作
        'NCD': {'C': 1.2, 'D': 2.8},  # 两次历史，对手先合作后背叛
        'NDC': {'C': 2.5, 'D': 3.8},  # 两次历史，对手先背叛后合作
        'NDD': {'C': 0.8, 'D': 1.8},  # 两次历史，对手连续背叛
    }
    
    # 保存Q值表到文件
    with open(model_path, 'wb') as f:
        pickle.dump(q_table, f)
    
    print(f"已创建Q-learning模型文件: {model_path}")
    print(f"包含 {len(q_table)} 个状态的Q值")
    
    return model_path

if __name__ == "__main__":
    model_path = create_q_learning_model()
    
    # 验证模型文件
    try:
        with open(model_path, 'rb') as f:
            q_table = pickle.load(f)
        print("\n验证成功，Q表内容:")
        for state, values in list(q_table.items())[:5]:  # 只显示前5个状态
            print(f"  {state}: {values}")
        print(f"  ... 共 {len(q_table)} 个状态")
    except Exception as e:
        print(f"验证失败: {str(e)}") 