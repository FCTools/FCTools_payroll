# Copyright © 2020-2021 Filthy Claws Tools - All Rights Reserved
#
# This file is part of FCTools_payroll
#
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Author: German Yakimov <german13yakimov@gmail.com>

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from django.urls import path, include

from fctools_salary.views import base_menu, count_view, LogoutView

urlpatterns = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + \
              static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
                  path("", base_menu, name="base_menu"),
                  path("count/", count_view, name="count"),
                  path("logout/", LogoutView.as_view(), name="logout"),
                  path("admin/", admin.site.urls),
                  path("login/", views.LoginView.as_view(), name="login"),
              ]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
