# Generated by Django 2.2.5 on 2019-09-10 05:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20190822_0439'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='secretary',
            field=models.ForeignKey(limit_choices_to={'groups__name': 'manager'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recordings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='union',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
