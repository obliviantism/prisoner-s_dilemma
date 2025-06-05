from django.core.management.base import BaseCommand
from dilemma_game.models import Tournament
from dilemma_game.services import TournamentService

class Command(BaseCommand):
    help = '重新计算指定锦标赛的对战矩阵'

    def add_arguments(self, parser):
        parser.add_argument('tournament_id', nargs='?', type=int, help='锦标赛ID')
        parser.add_argument('--all', action='store_true', help='重新计算所有已完成的锦标赛')

    def handle(self, *args, **options):
        tournament_id = options.get('tournament_id')
        recalculate_all = options.get('all', False)
        
        if recalculate_all:
            # 重新计算所有已完成的锦标赛
            tournaments = Tournament.objects.filter(status='COMPLETED')
            if not tournaments.exists():
                self.stdout.write(self.style.WARNING('没有找到已完成的锦标赛'))
                return
                
            for tournament in tournaments:
                self.recalculate_tournament(tournament)
                
            self.stdout.write(self.style.SUCCESS(f'成功重新计算了 {tournaments.count()} 个锦标赛的对战矩阵'))
        else:
            if not tournament_id:
                self.stdout.write(self.style.ERROR('缺少锦标赛ID参数，请提供ID或使用--all重新计算所有锦标赛'))
                return
                
            try:
                tournament = Tournament.objects.get(id=tournament_id)
            except Tournament.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'找不到ID为 {tournament_id} 的锦标赛'))
                return
                
            self.recalculate_tournament(tournament)
            
    def recalculate_tournament(self, tournament):
        """重新计算单个锦标赛的对战矩阵"""
        self.stdout.write(f'正在重新计算锦标赛"{tournament.name}" (ID: {tournament.id})的对战矩阵...')
        
        # 计算结果
        TournamentService.calculate_results(tournament)
        
        # 获取更新后的结果（包括对战矩阵）
        results = TournamentService.get_tournament_results(tournament)
        
        # 输出一些调试信息
        matrix = results.get('matchups_matrix', {})
        participants_count = len(tournament.participants.all())
        matrix_items = sum(1 for p1 in matrix.values() for _ in p1.items())
        
        self.stdout.write(f'  参赛者数量: {participants_count}')
        self.stdout.write(f'  矩阵项数量: {matrix_items}')
        
        # 检查矩阵是否完整
        expected_items = participants_count * participants_count
        if matrix_items < expected_items:
            self.stdout.write(self.style.WARNING(f'  警告: 矩阵不完整，预期 {expected_items} 项，但只有 {matrix_items} 项'))
            
            # 输出一些缺失的项
            for p1 in tournament.participants.all():
                for p2 in tournament.participants.all():
                    p1_name = p1.strategy.name
                    p2_name = p2.strategy.name
                    if p1_name not in matrix or p2_name not in matrix.get(p1_name, {}):
                        self.stdout.write(self.style.ERROR(f'  缺失: {p1_name} vs {p2_name}'))
        
        self.stdout.write(self.style.SUCCESS(f'锦标赛 "{tournament.name}" 结果重新计算完成!')) 