#!/usr/bin/env python
import json
import requests
import ast
from django.core.management.base import BaseCommand
from core.cloudfoundry import cf_login
from core.slack import slack_alert
from django.conf import settings


class bcolours:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_org_guid(cf_token, org_name):
    print(f"{bcolours.BOLD}Org Name: {bcolours.UNDERLINE}{org_name}{bcolours.ENDC}")
    response = requests.get(
        settings.CF_DOMAIN + "/v3/organizations",
        headers={"Authorization": f"Bearer {cf_token}"},
    )
    org_response = response.json()
    # breakpoint()
    for org in org_response['resources']:
        if org['name'] == org_name:
            org_guid = org['guid']
    return org_guid


def get_spaces(cf_token, org_guid):

    spaces = {}
    print(f"{bcolours.OKCYAN}Getting list of spaces{bcolours.ENDC}")
    response = requests.get(
        settings.CF_DOMAIN + "/v3/spaces",
        params={"organization_guids": [org_guid, ]},
        headers={"Authorization": f"Bearer {cf_token}"},
    )
    spaces_response = response.json()
    # breakpoint()
    for space in spaces_response['resources']:
        spaces[space['name']] = space['guid']

    return spaces


def get_log_drain_guid(cf_token, space_guid):
    log_drain_found = False
    print(f"{bcolours.OKCYAN}Getting guid for log-drain{bcolours.ENDC}")
    response = requests.get(
        settings.CF_DOMAIN + "/v3/service_instances",
        params={"space_guids": [space_guid, ]},
        headers={"Authorization": f"Bearer {cf_token}"},
    )
    service_response = response.json()
    # breakpoint()
    for service in service_response["resources"]:
        if service["name"] == "log-drain":
            log_drain_guid = service["guid"]
            log_drain_found = True

    if log_drain_found is False:
        log_drain_guid = 0
    # print(log_drain_guid)
    return log_drain_guid


def bind_app_to_log_drain(cf_token, log_drain_guid, app_name, app_guid):

    print(f"{bcolours.WARNING}Binding {app_name} to log drain{bcolours.ENDC}")
    json_data = {
        'type': 'app',
        'relationships': {
            'app': {
                'data': {
                    'guid': app_guid
                }
            },
            'service_instance': {
                'data': {
                    'guid': log_drain_guid
                }
            }
        }
    }
    # breakpoint()
    if settings.BIND_ENABLED == 'True':
        response = requests.post(
            settings.CF_DOMAIN + "/v3/service_bindings",
            headers={"Authorization": f"Bearer {cf_token}", "Content-Type": "application/json"},
            data=json.dumps(json_data),
        )
        bind_response = response.json()
        print(f"{bcolours.OKBLUE}{app_name} is now bound to: \
            {bind_response['data']['name']}{bcolours.ENDC}")
    else:
        print(f"{bcolours.OKBLUE}Running in demo mode {app_name} will NOT be bound")


class Command(BaseCommand):
    def handle(self, *args, **options):
        cf_client = cf_login()
        cf_token = cf_client._access_token

        no_log_drain_in_space = []
        apps_not_bound_to_log_drain = []
        slack_message = '```\nThis is the daily log-drain report.\n'

        for org in ast.literal_eval(settings.ORG_GUID):
            org_guid = get_org_guid(cf_token, org)

            spaces = get_spaces(cf_token, org_guid)
            print(spaces)
            # breakpoint()
            for space_name in spaces:
                print(f"{bcolours.HEADER}Checking Log Drains for space {space_name}...{bcolours.ENDC}")
                log_drain_guid = get_log_drain_guid(cf_token, spaces[space_name])
                if log_drain_guid != 0:
                    response = requests.get(
                        settings.CF_DOMAIN + "/v3/apps",
                        params={"space_guids": [spaces[space_name], ]},
                        headers={"Authorization": f"Bearer {cf_token}"},
                    )
                    app_response = response.json()

                    for app in app_response["resources"]:
                        logdrain_bound = False
                        response = requests.get(
                            settings.CF_DOMAIN + "/v3/service_bindings",
                            params={"app_guids": [app["guid"], ]},
                            headers={"Authorization": f"Bearer {cf_token}"},
                        )
                        # breakpoint()
                        service_response = response.json()
                        for service in service_response["resources"]:
                            if service["data"]["name"] == "log-drain":
                                print(f'{bcolours.OKGREEN}{bcolours.BOLD}{app["name"]}{bcolours.ENDC}{bcolours.OKGREEN} is bound to: {service["data"]["name"]}{bcolours.ENDC}')
                                logdrain_bound = True

                        if logdrain_bound is False:
                            print(f'{bcolours.FAIL}{app["name"]} is NOT bound to a log drain{bcolours.ENDC}')
                            # Only bind app if its not a conduit app.
                            if not app["name"].startswith("__conduit"):
                                apps_not_bound_to_log_drain.append(app["name"])
                                bind_app_to_log_drain(cf_token, log_drain_guid, app["name"], app["guid"])
                            else:
                                print(f'{bcolours.WARNING}This {app["name"]} will not be bound to log drain{bcolours.ENDC}')
                else:
                    # breakpoint()
                    print(f"{bcolours.FAIL}No log-drain found in this space{bcolours.ENDC}")
                    no_log_drain_in_space.append(space_name)
        
        if apps_not_bound_to_log_drain:
            slack_message += 'The following applications were NOT bound to a log-drain, but have now been programmatically bound:\n'
            for app in apps_not_bound_to_log_drain:
                slack_message += f'\n{app}'
        else:
            slack_message += 'All applications are bound to a log-drain.  Nothing to see here move along...'

        if no_log_drain_in_space:
            slack_message += '\n\nThe following spaces have a missing log-drain:\n'
            for space in no_log_drain_in_space:
                slack_message += f'\n{space}'
        slack_message += f'\n```'
        slack_alert(slack_message)
