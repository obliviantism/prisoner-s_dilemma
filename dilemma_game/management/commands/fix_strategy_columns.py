from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Add missing columns to the strategy table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if is_preset column exists
            cursor.execute("PRAGMA table_info(dilemma_game_strategy)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_preset' not in columns:
                self.stdout.write(self.style.WARNING('Adding is_preset column to strategy table...'))
                cursor.execute("ALTER TABLE dilemma_game_strategy ADD COLUMN is_preset BOOLEAN DEFAULT 0")
                self.stdout.write(self.style.SUCCESS('Successfully added is_preset column'))
            else:
                self.stdout.write(self.style.SUCCESS('is_preset column already exists'))
            
            if 'preset_id' not in columns:
                self.stdout.write(self.style.WARNING('Adding preset_id column to strategy table...'))
                cursor.execute("ALTER TABLE dilemma_game_strategy ADD COLUMN preset_id VARCHAR(50) NULL")
                self.stdout.write(self.style.SUCCESS('Successfully added preset_id column'))
            else:
                self.stdout.write(self.style.SUCCESS('preset_id column already exists')) 