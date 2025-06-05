from django.core.management.base import BaseCommand
from dilemma_game.models import Tournament, TournamentParticipant
from django.db import connection
import json

class Command(BaseCommand):
    help = '调试胜负平字段问题'

    def handle(self, *args, **options):
        self.stdout.write("开始诊断胜负平字段问题...")
        
        try:
            # 检查是否有完成的锦标赛
            tournaments = Tournament.objects.filter(status='COMPLETED')
            if not tournaments.exists():
                self.stdout.write(self.style.WARNING("没有找到已完成的锦标赛"))
                return
            
            # 获取第一个完成的锦标赛
            tournament = tournaments.first()
            self.stdout.write(f"检查锦标赛: {tournament.name} (ID: {tournament.id})")
            
            # 查看参赛者
            participants = TournamentParticipant.objects.filter(tournament=tournament)
            if not participants.exists():
                self.stdout.write(self.style.WARNING(f"锦标赛 {tournament.name} 没有参赛者"))
                return
            
            # 检查每个参赛者
            self.stdout.write("\n参赛者数据:")
            for p in participants:
                self.stdout.write(f"ID: {p.id}, 策略: {p.strategy.name}")
                self.stdout.write(f"  总分: {p.total_score}, 平均分: {p.average_score}, 排名: {p.rank}")
                self.stdout.write(f"  胜场数: {p.wins}, 类型: {type(p.wins)}")
                self.stdout.write(f"  平局数: {p.draws}, 类型: {type(p.draws)}")
                self.stdout.write(f"  负场数: {p.losses}, 类型: {type(p.losses)}")
            
            # 直接执行SQL查询
            self.stdout.write("\nSQL查询结果:")
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, strategy_id, wins, draws, losses FROM dilemma_game_tournamentparticipant WHERE tournament_id = %s", [tournament.id])
                rows = cursor.fetchall()
                for row in rows:
                    self.stdout.write(f"ID: {row[0]}, 策略ID: {row[1]}, 胜: {row[2]}, 平: {row[3]}, 负: {row[4]}")
            
            # 尝试直接更新一个参赛者
            if participants.exists():
                p = participants.first()
                
                # 打印原始值
                self.stdout.write(f"\n尝试更新参赛者 {p.strategy.name} (ID: {p.id})")
                self.stdout.write(f"更新前: 胜={p.wins}, 平={p.draws}, 负={p.losses}")
                
                # 直接设置值
                p.wins = 100
                p.draws = 50
                p.losses = 25
                p.save()
                
                # 重新获取并打印
                p_updated = TournamentParticipant.objects.get(id=p.id)
                self.stdout.write(f"更新后: 胜={p_updated.wins}, 平={p_updated.draws}, 负={p_updated.losses}")
                
                # 直接用SQL检查
                with connection.cursor() as cursor:
                    cursor.execute("SELECT wins, draws, losses FROM dilemma_game_tournamentparticipant WHERE id = %s", [p.id])
                    row = cursor.fetchone()
                    self.stdout.write(f"SQL查询结果: 胜={row[0]}, 平={row[1]}, 负={row[2]}")
            
            self.stdout.write(self.style.SUCCESS("\n诊断完成!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"诊断过程中出错: {str(e)}")) 