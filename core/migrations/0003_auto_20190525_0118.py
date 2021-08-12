# Generated by Django 2.2.1 on 2019-05-25 01:18

from django.db import migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20190525_0054'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='society',
            options={'verbose_name_plural': 'Societies'},
        ),
        migrations.AlterField(
            model_name='society',
            name='ref_number',
            field=django_extensions.db.fields.RandomCharField(blank=True, editable=False, length=5, unique=True, uppercase=True),
        ),
        migrations.AlterField(
            model_name='union',
            name='ref_number',
            field=django_extensions.db.fields.RandomCharField(blank=True, editable=False, length=5, unique=True, uppercase=True),
        ),
    ]
