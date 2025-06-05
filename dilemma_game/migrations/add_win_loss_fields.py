from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('dilemma_game', '0001_initial'),  # 根据实际情况调整依赖的迁移
    ]

    operations = [
        migrations.AddField(
            model_name='tournamentparticipant',
            name='wins',
            field=models.IntegerField(default=0, verbose_name='胜场数'),
        ),
        migrations.AddField(
            model_name='tournamentparticipant',
            name='draws',
            field=models.IntegerField(default=0, verbose_name='平局数'),
        ),
        migrations.AddField(
            model_name='tournamentparticipant',
            name='losses',
            field=models.IntegerField(default=0, verbose_name='负场数'),
        ),
    ] 