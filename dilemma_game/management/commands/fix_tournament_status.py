from django.core.management.base import BaseCommand
from dilemma_game.models import Tournament
from django.utils import timezone

class Command(BaseCommand):
    help = '检查并修复锦标赛状态'

    def handle(self, *args, **options):
        self.stdout.write("检查锦标赛状态...")
        
        # 获取所有锦标赛
        tournaments = Tournament.objects.all()
        
        if not tournaments.exists():
            self.stdout.write(self.style.WARNING("没有找到任何锦标赛"))
            return
            
        self.stdout.write(f"发现 {tournaments.count()} 个锦标赛:")
        
        for t in tournaments:
            self.stdout.write(f"ID: {t.id}, 名称: {t.name}, 状态: {t.status}, 创建时间: {t.created_at}")
            
            # 检查是否需要修复状态
            if t.status != 'COMPLETED':
                self.stdout.write(f"将锦标赛 '{t.name}' 的状态从 '{t.status}' 改为 'COMPLETED'")
                t.status = 'COMPLETED'
                if not t.completed_at:
                    t.completed_at = timezone.now()
                t.save()
                self.stdout.write(self.style.SUCCESS(f"锦标赛 '{t.name}' 状态已修复"))
        
        self.stdout.write(self.style.SUCCESS("所有锦标赛状态检查完成!")) 