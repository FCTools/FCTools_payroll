"""fctools_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views
from django.urls import path, include

from fctools_salary.views import base_menu, count_view, logout_view, update_db

urlpatterns = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + [
                  path('', base_menu, name='base_menu'),
                  path('count/', count_view, name='count'),
                  path('logout/', logout_view, name='logout'),
                  path('update_db/', update_db, name='update_db'),
                  path('admin/', admin.site.urls),
                  path('login/', views.LoginView.as_view(), name='login'),
              ]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
