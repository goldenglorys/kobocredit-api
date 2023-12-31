# Generated by Django 2.2.1 on 2019-06-04 16:12

import cloudinary.models
from django.db import migrations, models
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20190531_0007'),
    ]

    operations = [
        migrations.AlterField(
            model_name='society',
            name='ref_number',
            field=django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from=['union__name', 'name']),
        ),
        migrations.AlterField(
            model_name='union',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='union',
            name='ref_number',
            field=django_extensions.db.fields.AutoSlugField(blank=True, editable=False, populate_from=['name']),
        ),
        migrations.AlterField(
            model_name='user',
            name='picture',
            field=cloudinary.models.CloudinaryField(help_text='Profile picture', max_length=255, verbose_name='image'),
        ),
        migrations.AlterField(
            model_name='user',
            name='qrcode',
            field=cloudinary.models.CloudinaryField(help_text='Qrcode', max_length=255, null=True, verbose_name='image'),
        ),
    ]
