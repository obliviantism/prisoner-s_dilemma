from django.core.management.base import BaseCommand
from dilemma_game.models import Tournament

class Command(BaseCommand):
    help = '列出所有可用的锦标赛'

    def handle(self, *args, **options):
        self.stdout.write("列出所有锦标赛:")
        
        tournaments = Tournament.objects.all().order_by('id')
        
        if not tournaments.exists():
            self.stdout.write(self.style.WARNING("没有找到任何锦标赛"))
            return
        
        self.stdout.write("\n{:<5} {:<30} {:<15} {:<20}".format("ID", "名称", "状态", "创建时间"))
        self.stdout.write("-" * 70)
        
        for t in tournaments:
            self.stdout.write("{:<5} {:<30} {:<15} {:<20}".format(
                t.id, 
                t.name[:28] + '..' if len(t.name) > 30 else t.name,
                t.status,
                t.created_at.strftime('%Y-%m-%d %H:%M')
            ))
            
            # 显示参赛者数量
            participants_count = t.participants.count() if hasattr(t, 'participants') else 0
            self.stdout.write("      参赛者: {}".format(participants_count))
            
        self.stdout.write("\n总共 {} 个锦标赛".format(tournaments.count()))
        
        self.stdout.write(self.style.SUCCESS("\n要修复特定锦标赛，请运行:"))
        self.stdout.write("python manage.py recalc_tournament <锦标赛ID>") 