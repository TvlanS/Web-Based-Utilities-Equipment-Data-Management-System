from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.compressor_form ,name = 'compressor_insert'),
    path('list/',views.PM_list, name = "PM_list"),
    path('filter/',views.PM_filter, name = "PM_filter"),
    path('<int:id>/',views.compressor_form , name = "PM_filter_edit"),
    path('plot/', views.PM_plot, name = "PM_plot"),
    path('export/',views.export_excel , name = "export"),
    path('home/',views.Home,name = "home"),
    path("delete/<int:id>/",views.compressor_delete,name="PM_delete")
]