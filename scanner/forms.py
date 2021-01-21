from django import forms
from scanner.models import Applications, Spaces, Running
from django.core.management import call_command
from core.run_scan import runscan



def background_runscan():
    print("Running")
    runscan


class HomePageForm(forms.Form):

    # breakpoint()
    # if Running.objects.first().is_running:
    #     Running.objects.update_or_create(is_running=True, defaults={'is_running': False})
    # else:
    #     Running.objects.update_or_create(is_running=False, defaults={'is_running': True})
    # call_command('cf-log-drain-checker')

    background_runscan()
