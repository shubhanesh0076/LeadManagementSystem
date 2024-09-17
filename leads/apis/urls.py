
from django.urls import path
from leads.apis.views import FetchLeadAPIView, DynamicLeadFilterAPIView
app_name="leads-api"

urlpatterns = [
    path('', FetchLeadAPIView.as_view(), name='fetch-lead'),
    path('dynamic-lead-filter/', DynamicLeadFilterAPIView.as_view(), name='dynamic-lead-filter')
]