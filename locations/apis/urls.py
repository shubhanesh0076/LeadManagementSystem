# urls.py
from django.urls import path
from locations.apis.views import CountryCreateView, StateCreateView , CityCreateView

urlpatterns = [
    path('countries/', CountryCreateView.as_view(), name='country-create'),
    path('states/', StateCreateView.as_view(), name='state-create'),
    path('cities/', CityCreateView.as_view(), name='city-create'),
]
