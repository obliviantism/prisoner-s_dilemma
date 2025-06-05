from django.core.management.base import BaseCommand
from dilemma_game.models import Tournament, TournamentParticipant, Strategy
from django.contrib.auth.models import User
from django.utils import timezone
import random

class Command(BaseCommand):
    help = '创建测试锦标赛并设置胜负平数据'

    def handle(self, *args, **options):
        self.stdout.write("开始创建测试锦标赛...")
        
        try:
            # 获取一个用户
            users = User.objects.all()
            if not users.exists():
                self.stdout.write(self.style.ERROR("没有找到任何用户，无法创建锦标赛"))
                return
            user = users.first()
            
            # 创建锦标赛
            tournament_name = f"测试锦标赛-{random.randint(1000, 9999)}"
            tournament = Tournament.objects.create(
                name=tournament_name,
                description="这是一个用于测试胜负平数据的锦标赛",
                created_by=user,
                rounds_per_match=50,
                repetitions=2,
                status='COMPLETED',  # 直接设置为已完成
                created_at=timezone.now(),
                completed_at=timezone.now()
            )
            
            self.stdout.write(f"已创建锦标赛: {tournament.name} (ID: {tournament.id})")
            
            # 创建一些测试策略或使用现有策略
            strategies = Strategy.objects.all()
            if not strategies.exists():
                self.stdout.write("没有现有策略，创建测试策略...")
                strategy_names = ["测试策略A", "测试策略B", "测试策略C", "测试策略D"]
                for i, name in enumerate(strategy_names):
                    strategy = Strategy.objects.create(
                        name=name,
                        description=f"测试策略 {i+1}",
                        code="def make_move(history):\n    return 'C'",
                        created_by=user
                    )
                    self.stdout.write(f"已创建策略: {strategy.name}")
                strategies = Strategy.objects.filter(name__in=strategy_names)
            
            # 添加参赛者并设置胜负平数据
            for i, strategy in enumerate(strategies[:5]):  # 最多取5个策略
                participant = TournamentParticipant.objects.create(
                    tournament=tournament,
                    strategy=strategy,
                    total_score=random.randint(30000, 50000),
                    average_score=random.randint(400, 600),
                    rank=i+1,
                    wins=random.randint(50, 100),
                    draws=random.randint(20, 50),
                    losses=random.randint(10, 30)
                )
                self.stdout.write(f"已添加参赛者: {strategy.name}, 排名: {participant.rank}")
                self.stdout.write(f"  胜: {participant.wins}, 平: {participant.draws}, 负: {participant.losses}")
            
            self.stdout.write(self.style.SUCCESS(f"测试锦标赛 '{tournament.name}' 创建成功!"))
            self.stdout.write(f"请访问锦标赛结果页面: /tournaments/{tournament.id}/results/")
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"创建测试锦标赛时出错: {str(e)}")) 