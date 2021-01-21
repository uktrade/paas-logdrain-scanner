import requests

from django.shortcuts import render, redirect
from django.views import View
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.urls import reverse
from django.utils.decorators import method_decorator

from .forms import (HomePageForm)

from scanner.models import Applications, Spaces, Running

from django.contrib.auth.decorators import login_required

from django.template.loader import render_to_string
from django.http import HttpResponse


# @method_decorator(login_required, name='dispatch')
# class home_page(TemplateView):
#     template_name = 'home-page.html'
#
#     def get_context_data(self, **kwargs):
#         context = super(home_page, self).get_context_data(**kwargs)
#
#         context['applications'] = Applications.objects.all()
#         # breakpoint()
#         context['is_running'] = Running.objects.first()
#
#         return context

@method_decorator(login_required, name='dispatch')
class home_page(FormView):
    template_name = 'home-page.html'
    form_class = HomePageForm

    def get_context_data(self, **kwargs):
        context = super(home_page, self).get_context_data(**kwargs)
        context['applications'] = Applications.objects.all()
        # breakpoint()
        context['is_running'] = Running.objects.first()
        return context

    def form_valid(self, form):

        template = render_to_string('home-page.html')
        return HttpResponse(template)
