from django.urls import path
from . import views



urlpatterns = [
    path('', views.landing_page, name='landing'),  # Default landing page
    path('login/', views.user_login, name='login'),  # Login page
    path('register/', views.register_page, name='register'),  # Registration page
    path('home/', views.home, name='home'),  # Home page after login
    path('logout/', views.user_logout, name='logout'),  # Logout
    path('quiz/', views.quiz, name='quiz'),  # Quiz page
    path('leaderboard/', views.leaderboard, name='leaderboard'),  # Leaderboard
    path('results/', views.results, name='results'),  # Results page
    path('quiz/<str:video_id>/', views.video_quiz, name='video_quiz'),
    path("chatbot/", views.chatbot, name="chatbot"),
    path('resources/', views.input_topic, name='resources'),
    path('quiz/', views.quiz, name='quiz'),
    path('quiz_result/', views.quiz_result, name='quiz_result'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('results/', views.results, name='results'),
    
]
