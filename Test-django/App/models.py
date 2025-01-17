from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

class Image(models.Model):
    image = models.ImageField(upload_to='images/')


class Profile(models.Model):
    user = models.OneToOneField(User ,on_delete=models.CASCADE)
    forget_token = models.CharField(max_length=50)
    subscription_plan = models.CharField(max_length=50, default="Free")
    image_left = models.IntegerField(blank=False, null=False, default=5)
    images_generated = models.JSONField(default=list, blank=True)
    subscription_datetime = models.DateTimeField(blank=True, null=True,)
    
    
    def __str__(self):
        return self.user.username
    
