from django.urls import path
from . import views

urlpatterns = [
    # ── Public ──────────────────────────────────────
    path('', views.landing_page, name='landing'),

    # ── Auth ─────────────────────────────────────────
    path('register/', views.register_view, name='register'),
    path('login/',    views.login_view,    name='login'),
    path('logout/',   views.logout_view,   name='logout'),

    # ── Dashboard ─────────────────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),

    # ── Admin Registration Management ─────────────────
    path('dashboard/registrations/<int:profile_id>/',        views.admin_registration_detail, name='admin_registration_detail'),
    path('dashboard/registrations/<int:profile_id>/approve/', views.admin_approve_registration, name='admin_approve_registration'),
    path('dashboard/registrations/<int:profile_id>/reject/',  views.admin_reject_registration,  name='admin_reject_registration'),

    # ── Food Listings ─────────────────────────────────
    path('listings/create/',               views.create_listing, name='create_listing'),
    path('listings/<uuid:listing_id>/',    views.listing_detail, name='listing_detail'),

    # ── Match Workflow ────────────────────────────────
    path('matches/<uuid:match_id>/accept/',  views.accept_match,    name='accept_match'),
    path('matches/<uuid:match_id>/reject/',  views.reject_match,    name='reject_match'),
    path('matches/<uuid:match_id>/pickup/',  views.confirm_pickup,  name='confirm_pickup'),
    path('matches/<uuid:match_id>/verify/',  views.verify_delivery, name='verify_delivery'),

    # ── QR Code ──────────────────────────────────────
    path('matches/<uuid:match_id>/qr/',      views.match_qr,        name='match_qr'),

    # ── Digital Receipt ───────────────────────────────
    path('matches/<uuid:match_id>/receipt/', views.download_receipt, name='download_receipt'),

    # ── JSON API ──────────────────────────────────────
    path('api/listings/',                    views.api_listings,    name='api_listings'),
    path('api/impact/',                      views.api_impact,      name='api_impact'),
    path('api/matches/<uuid:match_id>/',     views.api_match_detail, name='api_match_detail'),
]

