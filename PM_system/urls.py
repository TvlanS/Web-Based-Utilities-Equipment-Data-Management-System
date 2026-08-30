from django.urls import path
from . import views

urlpatterns = [
    path('', views.root_redirect, name='root'),
    path('home/', views.home, name='home'),
    path('list/', views.compressor_list, name='PM_list'),
    path('filter/', views.compressor_filter, name='PM_filter'),
    path('plot/', views.compressor_plot, name='PM_plot'),
    path('export/', views.compressor_export, name='export'),
    path('delete/<int:id>/', views.compressor_delete, name='PM_delete'),
    path('forms/compressor/', views.compressor_form, name='compressor_insert'),
    path('<int:id>/', views.compressor_form, name='PM_filter_edit'),
]
