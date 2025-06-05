from django.core.management.base import BaseCommand
from dilemma_game.models import Tournament, TournamentParticipant, TournamentMatch
from django.db import transaction

class Command(BaseCommand):
    help = '重新计算特定锦标赛的胜负平数据'

    def add_arguments(self, parser):
        parser.add_argument('tournament_id', type=int, help='要重新计算的锦标赛ID')

    def handle(self, *args, **options):
        tournament_id = options['tournament_id']
        
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"找不到ID为{tournament_id}的锦标赛"))
            return
        
        self.stdout.write(f"开始重新计算锦标赛 '{tournament.name}' (ID: {tournament.id}) 的胜负平数据...")
        
        # 获取所有参赛者
        participants = TournamentParticipant.objects.filter(tournament=tournament)
        self.stdout.write(f"找到 {participants.count()} 个参赛者")
        
        with transaction.atomic():
            for p in participants:
                # 作为玩家1的比赛
                matches_as_p1 = TournamentMatch.objects.filter(
                    tournament=tournament,
                    participant1=p,
                    status='COMPLETED'
                )
                
                # 作为玩家2的比赛
                matches_as_p2 = TournamentMatch.objects.filter(
                    tournament=tournament,
                    participant2=p,
                    status='COMPLETED'
                )
                
                # 计算胜负平
                wins = 0
                draws = 0
                losses = 0
                
                # 作为玩家1的胜负平
                for match in matches_as_p1:
                    if match.player1_score > match.player2_score:
                        wins += 1
                    elif match.player1_score < match.player2_score:
                        losses += 1
                    else:
                        draws += 1
                
                # 作为玩家2的胜负平
                for match in matches_as_p2:
                    if match.player2_score > match.player1_score:
                        wins += 1
                    elif match.player2_score < match.player1_score:
                        losses += 1
                    else:
                        draws += 1
                
                # 更新参赛者
                p.wins = wins
                p.draws = draws
                p.losses = losses
                p.save()
                
                self.stdout.write(f"参赛者 {p.strategy.name}: 胜={wins}, 平={draws}, 负={losses}")
            
        self.stdout.write(self.style.SUCCESS(f"锦标赛 '{tournament.name}' 胜负平数据重新计算完成!")) 