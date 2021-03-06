# Generated by Django 2.2.9 on 2021-05-23 21:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_auto_20210521_2303'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='group',
            options={'verbose_name_plural': 'groups of posts'},
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-pub_date']},
        ),
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='gr', to='posts.Group'),
        ),
    ]
