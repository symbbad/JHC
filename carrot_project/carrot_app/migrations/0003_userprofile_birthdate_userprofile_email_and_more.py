# Generated by Django 4.2.5 on 2023-10-04 06:35

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('carrot_app', '0002_post_modified_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='birthdate',
            field=models.DateField(default=datetime.datetime(2023, 10, 4, 6, 34, 58, 751654, tzinfo=datetime.timezone.utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email',
            field=models.EmailField(default=datetime.datetime(2023, 10, 4, 6, 35, 5, 736181, tzinfo=datetime.timezone.utc), max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], default='O', max_length=1),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='nickname',
            field=models.CharField(default='Guest', max_length=100),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='profile_picture',
            field=models.ImageField(default='default_profile_picture.png', upload_to='profile_pictures/'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='user_certification',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='MannerTemperature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_votes', models.PositiveIntegerField(default=0)),
                ('total_score', models.PositiveIntegerField(default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='manner_temperature', to='carrot_app.userprofile')),
            ],
        ),
    ]
