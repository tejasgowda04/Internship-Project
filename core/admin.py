from django.contrib import admin
from .models import UserProfile, FoodListing, Match, DemandHistory, ImpactMetrics


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization_name', 'role', 'is_verified', 'created_at')
    list_filter = ('role', 'is_verified')
    search_fields = ('user__username', 'organization_name')


@admin.register(FoodListing)
class FoodListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'donor', 'food_type', 'quantity_kg', 'status', 'expiry_time', 'created_at')
    list_filter = ('status', 'food_type')
    search_fields = ('donor__username',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'listing', 'charity', 'match_score', 'status', 'blockchain_tx_hash', 'created_at')
    list_filter = ('status',)


@admin.register(DemandHistory)
class DemandHistoryAdmin(admin.ModelAdmin):
    list_display = ('charity', 'food_type', 'quantity_kg', 'timestamp')
    list_filter = ('food_type',)


@admin.register(ImpactMetrics)
class ImpactMetricsAdmin(admin.ModelAdmin):
    list_display = ('total_kg_saved', 'total_value_saved', 'total_matches', 'total_verifications', 'last_updated')
