from django.urls import path
from leads.apis.views import (
    FetchLeadAPIView,
    DynamicLeadFilterAPIView,
    LeadRemarkAPIView,
    LeadRemarkHistoryAPIView,
    AssignLeadAPIVIew,
    StatusWiseLeadAPIView,
    LeadDistributionAPIView,
    WeeklyNotificationsView
)

app_name = "leads-api"

urlpatterns = [
    path("", FetchLeadAPIView.as_view(), name="lead-info"),
    path("dynamic-lead-filter/",DynamicLeadFilterAPIView.as_view(),name="dynamic-lead-filter"),
    path("remark/", LeadRemarkAPIView.as_view(), name="lead-remark"),
    path("remark-history/", LeadRemarkHistoryAPIView.as_view(), name="remark-history"),
    path("assign/", AssignLeadAPIVIew.as_view(), name="assign-leads"),
    path('status-wise-lead/', StatusWiseLeadAPIView.as_view(), name="status-wise-lead"),
    path('distribution-to-user/', LeadDistributionAPIView.as_view(), name='lead-distribution'),
    
    #  path('notifications/mark-viewed/', MarkNotificationsAsViewed.as_view(), name='mark_notifications_as_viewed'),
    path('notifications/weekly/', WeeklyNotificationsView.as_view(), name='weekly_notifications'),
]
