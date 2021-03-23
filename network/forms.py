from django import forms
from django.forms import ModelForm
from network.models import Post, Profile


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = [
            'body'
        ]
        
        labels = {'body': "What's on your mind?"}

        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control body', 'rows': '3', 'columns': '15'})
        }

    