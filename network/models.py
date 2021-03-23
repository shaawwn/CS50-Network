from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Hold user information including: username, email, date joined, etc.  Full details in Django
    documentation"""
    pass


class Post(models.Model):
    """
    user: creator of the post
    body: body content of the post
    timestamp: date which post is created
    liked: Boolean value for if a user likes a post
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    body = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    # liked = models.BooleanField(default=False) Either a post is liked as a Boolean, or liked by a User
    # liked = models.ManyToManyField(User, blank=True, related_name="likes")
    liked = models.IntegerField(default=0)


    def serialize(self):
        """Convert to JSON for API calls"""
        return{
            "user": user.username,
            "body": body,
            "timestampe": timestamp.strftime("%b %d %Y, %I:%M %p"),
            "liked": liked
        }


    def __str__(self):
        return f"{self.user}: {self.body}"


class Profile(models.Model):
    """
    username: profile username
    user_following: ManyToManyField containing users that the profile user is following
    followed_by: ManyToManyField containing users that this user is being followed by
    liked_posts: ManyToManyField containing posts that the user has liked
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profile_user")
    user_following = models.ManyToManyField(User, blank=True, related_name="following")
    followed_by = models.ManyToManyField(User, blank=True, related_name="followed")
    liked_posts = models.ManyToManyField(Post, blank=True, related_name="liked_posts")


    def serialize(set):
        """Convert to JSON for API calls"""
        return{
            "id": self.id,
            "user": self.user.username,
            "following": self. following,
            "followed_by": self.followed_by
        }

    def __str__(self):
        return f"{self.user}"


    

