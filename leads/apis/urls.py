
from django.urls import path
from leads.apis.views import FetchLeadAPIView, DynamicLeadFilterAPIView, LeadRemarkAPIView, LeadRemarkHistoryAPIView, AssignLeadAPIVIew
app_name="leads-api"

urlpatterns = [
    path('', FetchLeadAPIView.as_view(), name='lead-info'),
    path('dynamic-lead-filter/', DynamicLeadFilterAPIView.as_view(), name='dynamic-lead-filter'),
    path('remark/', LeadRemarkAPIView.as_view(), name='lead-remark'),
    path('remark-history/', LeadRemarkHistoryAPIView.as_view(), name='remark-history'),
    path('assign-lead', AssignLeadAPIVIew.as_view(), name='assign-leads')
]