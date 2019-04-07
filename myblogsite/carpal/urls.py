from django.urls import path
from . import views

app_name = "carpal"
urlpatterns = [
    path('', views.index, name='index'),
    path('drunk/', views.drunk, name='drunk'),
    path('pothole/', views.pothole, name='pothole'),
    path('sheets/', views.get_sheet, name='sheets'),
    path('get-auth/', views.get_auth, name='auth'),
    path('after-auth/', views.after_auth, name='after_auth'),
]