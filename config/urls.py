"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("juego.urls")),
]


# ============================================================
# ARCHIVOS MEDIA
# ============================================================
# En Codespaces estamos usando DEBUG=False.
# Cuando DEV_TOOLS_ENABLED=True permitimos que Django
# sirva los archivos /media/ solo para pruebas.
# ============================================================

if getattr(settings, "DEV_TOOLS_ENABLED", False):
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {
                "document_root": settings.MEDIA_ROOT,
            },
        ),
    ]

elif settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )