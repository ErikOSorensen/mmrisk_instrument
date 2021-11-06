from django.urls import path
from . import views



urlpatterns = (path('login/', views.login),
               path('consent/', views.consent),
               path('instructions/', views.instructions),
               path('decision/', views.decision),
               path('question/', views.question),
               path('feedback/', views.feedback),

              )
