# Generated by Django 5.2 on 2025-04-21 19:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Letter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('letter_type', models.CharField(choices=[('text', 'Text'), ('image', 'Image'), ('pdf', 'PDF')], max_length=10)),
                ('text_content', models.TextField(blank=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='letters/')),
                ('pdf', models.FileField(blank=True, null=True, upload_to='letters/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('age', models.IntegerField()),
                ('gender', models.CharField(max_length=20)),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profiles/')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LetterLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('liked', models.BooleanField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('to_letter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.letter')),
                ('from_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_likes', to='core.profile')),
            ],
        ),
        migrations.AddField(
            model_name='letter',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.profile'),
        ),
    ]
