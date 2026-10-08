import os

from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage


class ConVersion(StaticFilesStorage):
    def url(self, name):
        url = super().url(name)
        ruta = finders.find(name)
        if ruta:
            url += f"?v={int(os.path.getmtime(ruta))}"
        return url
