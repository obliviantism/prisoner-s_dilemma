# Generated by Django 5.1.7

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dilemma_game', '0005_merge_20250605_1242'),
    ]

    operations = [
        migrations.AddField(
            model_name='strategy',
            name='is_preset',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='strategy',
            name='preset_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ] 