from django.contrib import admin
from .models import Account
from .forms import AccountCreationForm
from django.contrib.auth.admin import UserAdmin


class AccountAdmin(UserAdmin):
    add_form_template = 'admin/authentication/account/add_form.html'
    add_form = AccountCreationForm

# admin.site.register(Account, AccountAdmin)
