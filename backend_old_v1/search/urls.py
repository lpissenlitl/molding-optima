from django.urls import path

from search.views import *

urlpatterns = [
    path("search/options/", SelectOptionView.as_view()),
]
