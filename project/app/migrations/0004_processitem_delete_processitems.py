# Generated by Django 4.0.4 on 2022-04-20 16:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_item_name_alter_item_osrs_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('is_input', models.BooleanField()),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='process_items', to='app.item')),
                ('process', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='app.process')),
            ],
        ),
        migrations.DeleteModel(
            name='ProcessItems',
        ),
    ]
