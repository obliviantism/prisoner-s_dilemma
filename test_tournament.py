import os
import django
import sys
import json
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prisoners_dilemma.settings')
django.setup()

# 导入必要的模块
from dilemma_game.models import Strategy, Tournament, TournamentParticipant, TournamentMatch
from dilemma_game.services import TournamentService, GameService
from django.contrib.auth.models import User

def print_separator(message):
    """打印分隔符"""
    print("\n" + "="*50)
    print(f" {message} ")
    print("="*50 + "\n")

def test_tournament_creation():
    """测试创建锦标赛"""
    print_separator("测试创建锦标赛")
    
    # 获取或创建一个用户
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com', 'is_staff': True}
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f"创建了新用户: {user.username}")
    else:
        print(f"使用现有用户: {user.username}")
    
    # 创建一个新的锦标赛
    tournament = Tournament.objects.create(
        name=f"测试锦标赛 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        description="这是一个测试锦标赛",
        created_by=user,
        rounds_per_match=50,  # 设置较少的回合以加快测试
        repetitions=2,  # 设置较少的重复次数以加快测试
    )
    print(f"创建了新锦标赛: {tournament.name} (ID: {tournament.id})")
    
    return tournament

def add_participants_to_tournament(tournament):
    """向锦标赛添加参与者"""
    print_separator("向锦标赛添加参与者")
    
    # 获取所有策略
    strategies = Strategy.objects.all()
    print(f"找到 {strategies.count()} 个策略")
    
    # 添加所有策略作为参与者
    participants = []
    for strategy in strategies:
        participant, created = TournamentParticipant.objects.get_or_create(
            tournament=tournament,
            strategy=strategy
        )
        if created:
            print(f"添加了策略 '{strategy.name}' 到锦标赛")
        else:
            print(f"策略 '{strategy.name}' 已经在锦标赛中")
        participants.append(participant)
    
    return participants

def generate_and_play_matches(tournament):
    """生成并执行锦标赛比赛"""
    print_separator("生成并执行锦标赛比赛")
    
    # 生成比赛
    try:
        matches = TournamentService.generate_matches(tournament)
        print(f"生成了 {len(matches)} 场比赛")
        
        # 执行每场比赛
        for i, match in enumerate(matches):
            print(f"执行比赛 {i+1}/{len(matches)}: {match}")
            try:
                result = TournamentService.play_match(match)
                print(f"  结果: {result['player1']} ({result['player1_score']}) vs {result['player2']} ({result['player2_score']})")
            except Exception as e:
                print(f"  执行比赛失败: {e}")
        
        # 更新锦标赛状态为已完成
        tournament.status = 'COMPLETED'
        tournament.completed_at = datetime.now()
        tournament.save()
        print(f"锦标赛已完成")
        
    except Exception as e:
        print(f"生成或执行比赛时出错: {e}")

def get_tournament_results(tournament):
    """获取锦标赛结果"""
    print_separator("获取锦标赛结果")
    
    try:
        results = TournamentService.get_tournament_results(tournament)
        
        # 打印参与者排名
        print("参与者排名:")
        for i, participant in enumerate(results['participants']):
            print(f"{i+1}. {participant['strategy_name']}: {participant['average_score']} 分 (胜: {participant['wins']}, 平: {participant['draws']}, 负: {participant['losses']})")
        
        # 打印部分对战矩阵
        print("\n对战矩阵示例 (前3个策略):")
        strategies = list(results['matchups_matrix'].keys())[:3]
        for s1 in strategies:
            for s2 in strategies:
                matchup = results['matchups_matrix'][s1][s2]
                if isinstance(matchup, dict):
                    print(f"{s1} vs {s2}: 平均分 {matchup['avg_score']:.2f}, 胜/平/负: {matchup['wins']}/{matchup['draws']}/{matchup['losses']}")
                else:
                    print(f"{s1} vs {s2}: {matchup}")
        
    except Exception as e:
        print(f"获取锦标赛结果时出错: {e}")

def test_strategy_execution():
    """测试策略执行"""
    print_separator("测试策略执行")
    
    strategies = Strategy.objects.all()
    print(f"找到 {strategies.count()} 个策略")
    
    # 测试每个策略的执行
    for strategy in strategies:
        print(f"\n测试策略: {strategy.name} (ID: {strategy.id})")
        
        # 测试策略在不同历史记录下的选择
        empty_history = []
        all_c_history = ['C', 'C', 'C']
        all_d_history = ['D', 'D', 'D']
        mixed_history = ['C', 'D', 'C']
        
        try:
            choice1 = GameService.execute_strategy(strategy, empty_history)
            choice2 = GameService.execute_strategy(strategy, all_c_history)
            choice3 = GameService.execute_strategy(strategy, all_d_history)
            choice4 = GameService.execute_strategy(strategy, mixed_history)
            
            print(f"  空历史: {choice1}")
            print(f"  全合作历史: {choice2}")
            print(f"  全背叛历史: {choice3}")
            print(f"  混合历史: {choice4}")
        except Exception as e:
            print(f"  执行策略失败: {e}")

def main():
    """主函数"""
    print("开始锦标赛测试...")
    
    # 测试策略执行
    test_strategy_execution()
    
    # 创建锦标赛
    tournament = test_tournament_creation()
    
    # 添加参与者
    add_participants_to_tournament(tournament)
    
    # 生成并执行比赛
    generate_and_play_matches(tournament)
    
    # 获取结果
    get_tournament_results(tournament)
    
    print("\n锦标赛测试完成!")

if __name__ == "__main__":
    main() 