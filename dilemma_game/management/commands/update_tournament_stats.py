from django.core.management.base import BaseCommand
from dilemma_game.models import Tournament
from dilemma_game.services import TournamentService
from django.utils import timezone

class Command(BaseCommand):
    help = '重新计算所有已完成锦标赛的胜负平统计'

    def handle(self, *args, **options):
        # 获取所有已完成的锦标赛
        tournaments = Tournament.objects.filter(status='COMPLETED')
        total = tournaments.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('没有找到已完成的锦标赛'))
            return
        
        self.stdout.write(f'开始更新 {total} 个锦标赛的胜负平统计...')
        
        for i, tournament in enumerate(tournaments, 1):
            self.stdout.write(f'处理锦标赛 ({i}/{total}): {tournament.name}')
            
            # 重新计算锦标赛结果
            try:
                TournamentService.calculate_results(tournament)
                self.stdout.write(self.style.SUCCESS(f'成功更新锦标赛 {tournament.name} 的胜负平统计'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'更新锦标赛 {tournament.name} 失败: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'完成! 已更新 {total} 个锦标赛的胜负平统计')) 