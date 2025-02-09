# Generated by Django 4.2.10 on 2024-03-31 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LittleLemonAPI', '0003_alter_orderitem_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='title',
            field=models.CharField(db_index=True, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='title',
            field=models.CharField(db_index=True, max_length=255, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='orderitem',
            unique_together={('menuitem',)},
        ),
    ]
