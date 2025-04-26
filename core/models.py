from django.db import models

from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    preferred_gender = models.CharField(max_length=20, blank=True, null=True)
    preferred_age_min = models.IntegerField(blank=True, null=True)
    preferred_age_max = models.IntegerField(blank=True, null=True)
class Letter(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    letter_type = models.CharField(max_length=10, choices=[('text', 'Text'), ('image', 'Image'), ('pdf', 'PDF')])
    text_content = models.TextField(blank=True)
    image = models.ImageField(upload_to='letters/', blank=True, null=True)
    pdf = models.FileField(upload_to='letters/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class LetterLike(models.Model):
    from_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='from_likes')
    to_letter = models.ForeignKey(Letter, on_delete=models.CASCADE)
    liked = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Match(models.Model):
    user1 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='match_user1')
    user2 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='match_user2')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')

class Message(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.user.username} to {self.receiver.user.username}"