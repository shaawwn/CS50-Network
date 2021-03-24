from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from .models import User, Post, Profile
from . import forms
import json


def index(request):
    user = request.user
    return render(request, "network/index.html", {
        "user": user
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()

            # Create Profile associated with username
            profile = Profile()
            profile.user = user
            profile.save()

        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


# ---------------------------------------------------- PAGE DISPLAY FUNCTIONS --------------------------------------------
"""
Functions for loading and rendering All, Profile, and Following pages
"""
def get_all(request):
    """Render All posts page"""
    form = forms.PostForm

    # Load Post content
    posts = display_posts(request, 'get_all')
    # Pagination 
    post_paginator = Paginator(posts, 10)
    page_num = request.GET.get('page')
    page = post_paginator.get_page(page_num)

    return render(request, "network/all.html", {
        "form": form,
        # "posts": posts,
        "page": page
    })


def get_following(request):
    """Render Following page"""

    # Get the users that current_user is following
    current_user = User.objects.get(username=request.user.username)
    current_user_profile = Profile.objects.get(user=current_user)
    users_following = current_user_profile.user_following.all()

    # Check how many followers/following
    # print(len(users_following))
    # print(users_following)

    # Get posts from following
    posts = display_posts(request, {'get_following': users_following})

    # Pagination
    post_paginator = Paginator(posts, 10)
    page_num = request.GET.get('page')
    page = post_paginator.get_page(page_num)

    return render(request, "network/following.html", {
        "page": page
    })


def profile(request, username):
    """Render user profile page, including a form to create posts if the profile is current user profile"""
    form = forms.PostForm
    posts = display_posts(request, {'profile': username})
    current_user = User.objects.get(username=request.user.username) # Current user

    # Check if current users profile, if not add the ability to follow user
    if request.user.username != username:
        # If the profile is NOT current_user's

        user = User.objects.get(username=username) # User to follow
        following_list = Profile.objects.get(user=current_user) # List of profile current user followers
        user_followed_by = Profile.objects.get(user=user) # List of users following the profile user

        # Manage current_user following (If following the follow button = Unfollow, vice versa) and set a boolean for follow/not follow
        if user in following_list.user_following.all():
            watching = True
        else:
            watching = False
        
        # When current user clicks Follow button (or Unfollow), it updates the database
        if request.method == 'POST':
            if watching == True:

                # Remove user from current_users following and current_user from user's followers
                following_list.user_following.remove(user)
                user_followed_by.followed_by.remove(current_user)
                # Set flag to "Not following"
                watching = False
            else:
                # Add user to current_user's followers, and add current_user to user's followers
                following_list.user_following.add(user)
                user_followed_by.followed_by.add(current_user)
                watching = True
        
        # Save the new entries
        following_list.save()
        user_followed_by.save()
        print("Current user is following:", following_list.user_following.all())
        # print("Number following:", len(following_list.user_following.all()))
        print("Profile user is being followed by: ", user_followed_by.followed_by.all())
        # num_followers = len(following_list.user_following.all())
        num_followers = len(user_followed_by.followed_by.all())

    else:
        # Curret User's profile page, does not include ability to follow, but does have the # of followers.
        following_list = Profile.objects.get(user=current_user) # List of current user followers
        print(following_list.user_following.all())
        num_followers = len(following_list.followed_by.all())
        
        print("Current user is following:", following_list.user_following.all())
        print("Current user is being followed by: ", following_list.followed_by.all())
        watching = None

    # Pagination
    post_paginator = Paginator(posts, 10)
    page_num = request.GET.get('page')
    page = post_paginator.get_page(page_num)

    num_following = None
    return render(request, "network/profile.html", {
        "form": form,
        "posts": posts,
        "page": page,
        "username": username,
        "watching": watching,
        "num_followers": num_followers
    })



# -------------------------------------------------------POST FUNCTIONS ---------------------------------------------------
"""
Includes function(s) for craeting user posts and updating db
"""

@csrf_exempt
@login_required
def create_post(request):
    """Submit a post"""
    print("Even loading")
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)
    print("Gets past POST check")
    data = json.loads(request.body)
    body = data.get("body", "")
    print("Gets past request")
    new_post = Post(
        user=request.user,
        body=body
    )
    print("Creates the post")
    new_post.save()
    print("Gets past post.save()")
    return JsonResponse({"message": "Post successfully uploaded"}, status=201)

# ----------------------------------------------------- LOAD POSTS ----------------------------
"""
Includes functions for the actual loading of posts from the DB.
"""

def display_posts(request, request_type=None):
    """Should return a list of posts per the given parameter, all retrieve all
    following retrieves following posts, username retrieves users posts.
    """
    if request_type == None:
        raise Exception("You have recieved me in error!")
    if request_type == 'get_all':
        posts = Post.objects.all()

    elif [key for key in request_type.keys()][0] == 'get_following':
        posts = Post.objects.none()
        for user in request_type['get_following']:
            user_posts = Post.objects.filter(user=user)
            posts = posts.union(user_posts)

    elif  [key for key in request_type.keys()][0] == 'profile':
        # Gets posts for a given user

        user = User.objects.get(username=request_type['profile'])
        posts = Post.objects.filter(user=user)

    return posts.order_by("-timestamp").all()


@login_required
def get_post(request, post_id):
    """Get an indivual post by post id"""
    print("At least it is loading et post...>?")
    if request.method == 'PUT':
        data = json.loads(request.body)
        body = data.get("body", "")

        # Get original post
        post = Post.objects.get(id=post_id)
        post.body = body
        post.save()
        return JsonResponse({"message": "Post successfully updated"}, status=201)
    else:
        post = Post.objects.get(id=post_id)
        return JsonResponse(post.serialize(), safe=False)



# ------------------------------------------------------ PROFILE FUNCTIONS ------------------------------------------------





















# ----------------------------------- TESTING FUNCTIONS -----------------------------------------

# PAGINATION

# def get_all(request):
#     """Display All posts page"""
#     form = forms.PostForm

#     # Pagination 
#     test_list = list(range(1, 100))
#     test_paginator = Paginator(test_list, 10)
#     page_num = request.GET.get('page')
#     page = test_paginator.get_page(page_num)

#     return render(request, "network/all.html", {
#         "form": form,
#         "count": test_paginator.count,
#         "page": page,
#     })


# def like_posts(request, post_id):
#     """Allow a user to like a post and add it to that user's liked post attribute"""
    
#     " Get the post using the post id and current user"
#     post = Post.objects.get(id=post_id)
#     current_user = User.objects.get(username=request.user.username)
#     user_profile = Profile.objects.get(user=current_user)

#     user_liked = Profile.liked_posts.all()
#     # Add post to users 'liked_posts' attribute
#     user_profile.liked_posts.add(post)
#     user_profile.save()

# def profile(request, username):
#     """Render user profile page, including a form to create posts if the profile is current user profile"""
#     form = forms.PostForm
#     posts = display_posts(request, {'profile': username})
#     current_user = User.objects.get(username=request.user.username) # Current user

#     # Check if current users profile, if not add the ability to follow user
#     if request.user.username != username:
#         # If the profile is NOT current_user's

#         user = User.objects.get(username=username) # User to follow
#         following_list = Profile.objects.get(user=current_user) # List of profile current user followers
#         user_followed_by = Profile.objects.get(user=user) # List of users following the profile user

#         # Manage current_user following (If following the follow button = Unfollow, vice versa) and set a boolean for follow/not follow
#         if user in following_list.user_following.all():
#             watching = True
#         else:
#             watching = False
        
#         # When current user clicks Follow button (or Unfollow), it updates the database
#         if request.method == 'POST':
#             if watching == True:

#                 # Remove user from current_users following and current_user from user's followers
#                 following_list.user_following.remove(user)
#                 user_followed_by.followed_by.remove(current_user)
#                 # Set flag to "Not following"
#                 watching = False
#             else:
#                 # Add user to current_user's followers, and add current_user to user's followers
#                 following_list.user_following.add(user)
#                 user_followed_by.followed_by.add(current_user)
#                 watching = True
        
#         # Save the new entries
#         following_list.save()
#         user_followed_by.save()
#         print("Current user is following:", following_list.user_following.all())
#         # print("Number following:", len(following_list.user_following.all()))
#         print("Profile user is being followed by: ", user_followed_by.followed_by.all())
#         # num_followers = len(following_list.user_following.all())
#         num_followers = len(user_followed_by.followed_by.all())

#     else:
#         # Curret User's profile page, does not include ability to follow, but does have the # of followers.
#         following_list = Profile.objects.get(user=current_user) # List of current user followers
#         print(following_list.user_following.all())
#         num_followers = len(following_list.followed_by.all())
        
#         print("Current user is following:", following_list.user_following.all())
#         print("Current user is being followed by: ", following_list.followed_by.all())
#         watching = None

#     # Pagination
#     post_paginator = Paginator(posts, 10)
#     page_num = request.GET.get('page')
#     page = post_paginator.get_page(page_num)

#     num_following = None
#     return render(request, "network/profile.html", {
#         "form": form,
#         "posts": posts,
#         "page": page,
#         "username": username,
#         "watching": watching,
#         "num_followers": num_followers
#     })