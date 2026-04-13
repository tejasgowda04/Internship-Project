"""
AI Matching Engine
Scores and ranks charities for each food listing using:
  - Proximity (40%): OSRM road distance
  - Need Score (40%): ML-predicted demand
  - Capacity (20%): Historical acceptance rate
"""
import logging
from django.contrib.auth.models import User
from core.models import UserProfile, Match, FoodListing
from core.services.geo_service import filter_charities_by_radius, get_route_details
from core.services.ml_forecast import calculate_need_score

logger = logging.getLogger(__name__)

MAX_RADIUS_KM = 25  # Only match charities within 25km


def score_charity(donor_profile, charity_user, food_type=None):
    """
    Score a single charity for a donor listing.
    Returns dict with all scoring components + final score.
    """
    charity_profile = charity_user.profile

    # 1. Proximity score (closer = higher score)
    route = get_route_details(
        donor_profile.latitude, donor_profile.longitude,
        charity_profile.latitude, charity_profile.longitude
    )
    road_km = route['road_km']

    if road_km <= 2:
        proximity_score = 1.0
    elif road_km <= 5:
        proximity_score = 0.85
    elif road_km <= 10:
        proximity_score = 0.65
    elif road_km <= 15:
        proximity_score = 0.45
    elif road_km <= 25:
        proximity_score = 0.25
    else:
        proximity_score = 0.1

    # 2. Need score from ML service
    need_score = calculate_need_score(charity_user, food_type)

    # 3. Capacity score (based on acceptance and completion rate)
    total_matches = Match.objects.filter(charity=charity_user).count()
    accepted = Match.objects.filter(charity=charity_user, status__in=['accepted', 'picked_up', 'verified']).count()

    if total_matches > 0:
        acceptance_rate = accepted / total_matches
        capacity_score = min(acceptance_rate, 1.0)
    else:
        capacity_score = 0.7  # New charities get decent default

    # Composite score
    match_score = (0.4 * proximity_score) + (0.4 * need_score) + (0.2 * capacity_score)

    return {
        'charity': charity_user,
        'proximity_score': round(proximity_score, 3),
        'need_score': round(need_score, 3),
        'capacity_score': round(capacity_score, 3),
        'match_score': round(match_score, 3),
        'road_km': road_km,
        'haversine_km': route['haversine_km'],
        'duration_min': route['duration_min'],
    }


def find_best_match(listing):
    """
    Find and create the best charity match for a food listing.
    Returns the created Match object or None.
    """
    donor_profile = listing.donor.profile

    # Get all verified charities
    charities = User.objects.filter(
        profile__role='charity',
        profile__is_verified=True
    ).select_related('profile')

    if not charities.exists():
        # Fallback: also include unverified charities
        charities = User.objects.filter(
            profile__role='charity'
        ).select_related('profile')

    # Step 1: Haversine filter (within radius)
    nearby = filter_charities_by_radius(
        donor_profile.latitude, donor_profile.longitude,
        charities, MAX_RADIUS_KM
    )

    if not nearby:
        logger.warning(f"No charities within {MAX_RADIUS_KM}km of listing {listing.id}")
        return None

    # Step 2: Score each remaining charity
    scored = []
    for charity_user, h_dist in nearby:
        # Skip already-matched charities for this listing
        if Match.objects.filter(listing=listing, charity=charity_user).exists():
            continue
        score_data = score_charity(donor_profile, charity_user, listing.food_type)
        scored.append(score_data)

    if not scored:
        logger.warning(f"No eligible charities for listing {listing.id}")
        return None

    # Step 3: Rank by composite score
    scored.sort(key=lambda x: x['match_score'], reverse=True)
    best = scored[0]

    # Step 4: Create Match record
    match = Match.objects.create(
        listing=listing,
        charity=best['charity'],
        distance_km=best['haversine_km'],
        road_distance_km=best['road_km'],
        need_score=best['need_score'],
        match_score=best['match_score'],
        status='pending'
    )

    # Update listing status
    listing.status = 'matched'
    listing.save()

    logger.info(
        f"Match created: {listing.id} → {best['charity'].username} "
        f"(score: {best['match_score']}, dist: {best['road_km']}km)"
    )

    return match


def get_ranking_for_listing(listing, limit=5):
    """
    Get top N charity rankings for a listing (for admin view).
    Returns list of score dicts.
    """
    donor_profile = listing.donor.profile
    charities = User.objects.filter(
        profile__role='charity'
    ).select_related('profile')

    nearby = filter_charities_by_radius(
        donor_profile.latitude, donor_profile.longitude,
        charities, MAX_RADIUS_KM
    )

    scored = []
    for charity_user, h_dist in nearby:
        score_data = score_charity(donor_profile, charity_user, listing.food_type)
        scored.append(score_data)

    scored.sort(key=lambda x: x['match_score'], reverse=True)
    return scored[:limit]
