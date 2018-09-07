from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from .models import Account


class AccountCreationForm(UserCreationForm):

    class Meta:
        model = Account
        fields = ("username",)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if Account.objects.filter(username=username).count() == 0:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
            )
