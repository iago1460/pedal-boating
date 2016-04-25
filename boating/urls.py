"""hire_point_booking URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from boating.views import HomeView, BookingView, BookingSuccessfulView, BookingUnsuccessfulView

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', HomeView.as_view(),  name='home'),
    url(r'^hire_point/(?P<pk>\d+)/$', BookingView.as_view(),  name='booking'),
    url(r'^booking/(?P<pk>\d+)/$', BookingSuccessfulView.as_view(),  name='booking_successful'),
    url(r'^booking/fail/$', BookingUnsuccessfulView.as_view(),  name='booking_unsuccessful'),
]
