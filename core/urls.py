# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('letters/', views.browse_letter, name='browse_letter'),
    path('react/<int:letter_id>/', views.react_to_letter, name='react_to_letter'),
    path('upload/', views.upload_letter, name='upload_letter'),
    path('matches/', views.view_matches, name='view_matches'),
    path('messages/<int:profile_id>/', views.message_view, name='message_view'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('register/', views.register, name='register'),
    path('profile/', views.view_profile, name='view_profile'),

    # ✅ Letter edit/delete
    path('letter/edit/<int:letter_id>/', views.edit_letter, name='edit_letter'),
    path('letter/delete/<int:letter_id>/', views.delete_letter, name='delete_letter'),

    # ✅ Likes and matches
    path('likes/', views.likes_received, name='likes_received'),
    path('like_back/<int:profile_id>/', views.like_back, name='like_back'),
    path('reject_like/<int:profile_id>/', views.reject_like, name='reject_like'),
    path('unmatch/<int:profile_id>/', views.unmatch, name='unmatch'),

    # ✅ Images
    path('letter/image/delete/<int:image_id>/', views.delete_letter_image, name='delete_letter_image'),
    path('letter/add_images/<int:letter_id>/', views.add_letter_images, name='add_letter_images'),  # ➕ New!
    path('notifications/', views.notifications_view, name='notifications'),
path('matched-profile/<int:profile_id>/', views.matched_profile_view, name='matched_profile'),
path('chats/', views.chat_list_view, name='chat_list'),

]
