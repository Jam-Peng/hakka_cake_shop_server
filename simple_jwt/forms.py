from django.contrib.auth.forms import UserCreationForm
from .models import Staff


class MyUserCreationForm(UserCreationForm):

    class Meta:
        model = Staff
        fields = ['name', 'username', 'email', 'password1']

