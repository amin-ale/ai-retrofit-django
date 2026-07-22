from django.conf import settings


def copilot_settings():
    return settings.COPILOT


def get(key):
    return settings.COPILOT[key]
