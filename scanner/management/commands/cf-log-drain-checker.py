#!/usr/bin/env python
import json
import requests
import ast
import time
from django.core.management.base import BaseCommand
from core.cloudfoundry import cf_login
from core.slack import slack_alert
from django.conf import settings

from scanner.models import Applications, Spaces, Running
from core.run_scan import runscan

class Command(BaseCommand):
    def handle(self, *args, **options):
        runscan()
