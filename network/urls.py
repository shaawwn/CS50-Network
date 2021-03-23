
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("all", views.get_all, name="all"),
    path("following", views.get_following, name="following"),
    path("profile/<str:username>", views.profile, name="profile"),

    # API CALLS
    path("post", views.create_post, name="create_post"),
    path("posts", views.display_posts, name="display_posts"),
    path("posts/<int:post_id>", views.get_post, name="get_post"),
]
