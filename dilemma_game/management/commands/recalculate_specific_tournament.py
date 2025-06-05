from django.core.management.base import BaseCommand
from dilemma_game.models import Tournament, TournamentParticipant, TournamentMatch
from django.db import transaction
from django.utils import timezone

class Command(BaseCommand):
    help = '重新计算特定锦标赛的结果，特别是胜负平数据'

    def add_arguments(self, parser):
        parser.add_argument('tournament_id', type=int, help='要重新计算的锦标赛ID')

    def handle(self, *args, **options):
        tournament_id = options['tournament_id']
        
        try:
            tournament = Tournament.objects.get(id=tournament_id)
        except Tournament.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"找不到ID为{tournament_id}的锦标赛"))
            return
        
        self.stdout.write(f"开始重新计算锦标赛 '{tournament.name}' (ID: {tournament.id}) 的结果...")
        
        # 设置锦标赛状态为已完成
        if tournament.status != 'COMPLETED':
            self.stdout.write(f"将锦标赛状态从 '{tournament.status}' 修改为 'COMPLETED'")
            tournament.status = 'COMPLETED'
            tournament.completed_at = tournament.completed_at or timezone.now()
            tournament.save()
        
        # 获取所有参赛者
        participants = TournamentParticipant.objects.filter(tournament=tournament)
        self.stdout.write(f"找到 {participants.count()} 个参赛者")
        
        try:
            with transaction.atomic():
                # 对每个参赛者重新计算得分和胜负平
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
                    
                    # 计算总分和比赛数
                    total_score = sum(m.player1_score for m in matches_as_p1) + sum(m.player2_score for m in matches_as_p2)
                    total_matches = matches_as_p1.count() + matches_as_p2.count()
                    
                    # 计算胜负平
                    wins = 0
                    losses = 0
                    draws = 0
                    
                    # 计算作为玩家1的胜负平
                    for match in matches_as_p1:
                        if match.player1_score > match.player2_score:
                            wins += 1
                        elif match.player1_score < match.player2_score:
                            losses += 1
                        else:
                            draws += 1
                    
                    # 计算作为玩家2的胜负平
                    for match in matches_as_p2:
                        if match.player2_score > match.player1_score:
                            wins += 1
                        elif match.player2_score < match.player1_score:
                            losses += 1
                        else:
                            draws += 1
                    
                    # 计算平均分
                    average_score = total_score / total_matches if total_matches > 0 else 0
                    
                    # 更新参赛者的分数和胜负平
                    self.stdout.write(f"更新参赛者 '{participant.strategy.name}':")
                    self.stdout.write(f"  总分: {participant.total_score} → {total_score}")
                    self.stdout.write(f"  平均分: {participant.average_score} → {average_score}")
                    self.stdout.write(f"  胜场数: {participant.wins} → {wins}")
                    self.stdout.write(f"  平局数: {participant.draws} → {draws}")
                    self.stdout.write(f"  负场数: {participant.losses} → {losses}")
                    
                    participant.total_score = total_score
                    participant.average_score = average_score
                    participant.wins = wins
                    participant.draws = draws
                    participant.losses = losses
                    
                    # 暂时不保存，待排名计算后一起保存
                
                # 根据平均分对参赛者排名
                ranked_participants = sorted(participants, key=lambda p: p.average_score, reverse=True)
                
                # 更新排名并保存
                for rank, participant in enumerate(ranked_participants, 1):
                    old_rank = participant.rank
                    participant.rank = rank
                    self.stdout.write(f"参赛者 '{participant.strategy.name}' 排名: {old_rank} → {rank}")
                    participant.save()
                
                # 检查对战矩阵
                self.stdout.write("\n检查对战矩阵数据:")
                for p1 in participants:
                    for p2 in participants:
                        # 获取p1和p2之间的所有比赛
                        matches = TournamentMatch.objects.filter(
                            tournament=tournament,
                            participant1=p1,
                            participant2=p2,
                            status='COMPLETED'
                        )
                        
                        if matches.exists():
                            # 计算总分和胜负平
                            total_score = sum(m.player1_score for m in matches)
                            avg_score = total_score / matches.count()
                            wins = sum(1 for m in matches if m.player1_score > m.player2_score)
                            draws = sum(1 for m in matches if m.player1_score == m.player2_score)
                            losses = sum(1 for m in matches if m.player1_score < m.player2_score)
                            
                            self.stdout.write(f"  {p1.strategy.name} vs {p2.strategy.name}: "
                                      f"平均={avg_score:.2f}, 胜={wins}, 平={draws}, 负={losses}, 总场次={matches.count()}")
                
                self.stdout.write(self.style.SUCCESS(f"\n锦标赛 '{tournament.name}' 结果重新计算完成!"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"重新计算过程中出错: {str(e)}"))
            raise 