from django.core.management.base import BaseCommand
from dilemma_game.models import Tournament, TournamentParticipant, TournamentMatch
from django.db import transaction

class Command(BaseCommand):
    help = '直接修复锦标赛的胜负平统计数据'

    def handle(self, *args, **options):
        # 获取所有已完成的锦标赛
        tournaments = Tournament.objects.filter(status='COMPLETED')
        total = tournaments.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('没有找到已完成的锦标赛'))
            return
        
        self.stdout.write(f'开始修复 {total} 个锦标赛的胜负平统计...')
        
        for i, tournament in enumerate(tournaments, 1):
            self.stdout.write(f'处理锦标赛 ({i}/{total}): {tournament.name}')
            
            try:
                with transaction.atomic():
                    # 获取所有参赛者
                    participants = TournamentParticipant.objects.filter(tournament=tournament)
                    
                    for participant in participants:
                        # 作为玩家1的比赛
                        matches_as_p1 = TournamentMatch.objects.filter(
                            tournament=tournament,
                            participant1=participant,
                            status='COMPLETED'
                        )
                        
                        # 作为玩家2的比赛
                        matches_as_p2 = TournamentMatch.objects.filter(
                            tournament=tournament,
                            participant2=participant,
                            status='COMPLETED'
                        )
                        
                        # 计算胜负平
                        wins = 0
                        losses = 0
                        draws = 0
                        
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
                        
                        # 直接更新数据库记录
                        participant.wins = wins
                        participant.draws = draws
                        participant.losses = losses
                        participant.save()
                        
                        self.stdout.write(f'  参赛者 {participant.strategy.name}: 胜={wins}, 平={draws}, 负={losses}')
                
                self.stdout.write(self.style.SUCCESS(f'成功修复锦标赛 {tournament.name} 的胜负平统计'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'修复锦标赛 {tournament.name} 失败: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'完成! 已修复 {total} 个锦标赛的胜负平统计')) 