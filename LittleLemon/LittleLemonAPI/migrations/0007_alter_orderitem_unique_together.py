# Generated by Django 4.2.10 on 2024-03-31 05:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('LittleLemonAPI', '0006_alter_orderitem_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='orderitem',
            unique_together={('order', 'menuitem')},
        ),
    ]
