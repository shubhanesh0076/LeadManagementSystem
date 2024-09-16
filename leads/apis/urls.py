
from django.urls import path
from leads.apis.views import FetchLeadAPIView
app_name="leads-api"

urlpatterns = [
    path('', FetchLeadAPIView.as_view(), name='fetch-lead')
]