"""
FoodWasteChain Views
Handles all page rendering, auth flows, CRUD, and API endpoints.
All features:
  - Auth (register / login / logout)
  - Role-based dashboards (donor / charity / admin)
  - Food listing CRUD with AI matching on create
  - Match workflow (accept → pickup → verify)
  - Blockchain verification on delivery
  - QR code generation (unique per match)
  - Digital PDF receipt download
  - Email notifications at every stage
  - Geo-based charity matching with OSRM distances
  - ML demand forecasting for charities
"""
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.views.decorators.http import require_POST

from .models import UserProfile, FoodListing, Match, DemandHistory, ImpactMetrics
from .forms import RegistrationForm, LoginForm, FoodListingForm, DeliveryPhotoForm
from .decorators import donor_required, charity_required, admin_required

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════
#  AUTH VIEWS
# ═══════════════════════════════════════════════════

def landing_page(request):
    """Public landing page with impact metrics."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    metrics = ImpactMetrics.get_metrics()
    recent_listings = FoodListing.objects.filter(status='available')[:6]

    return render(request, 'core/landing.html', {
        'metrics': metrics,
        'recent_listings': recent_listings,
    })


def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = User.objects.create_user(
                username=cd['username'],
                email=cd['email'],
                password=cd['password'],
            )
            UserProfile.objects.create(
                user=user,
                role=cd['role'],
                organization_name=cd['organization_name'],
                phone=cd.get('phone', ''),
                address=cd.get('address', ''),
                latitude=cd.get('latitude', 12.9716),
                longitude=cd.get('longitude', 77.5946),
            )
            # Update impact metrics
            metrics = ImpactMetrics.get_metrics()
            if cd['role'] == 'donor':
                metrics.total_donors += 1
            else:
                metrics.total_charities += 1
            metrics.save()

            login(request, user)
            messages.success(request, f"Welcome to FoodWasteChain, {cd['organization_name']}!")
            return redirect('dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Allow login by email too
            if '@' in username:
                try:
                    user_obj = User.objects.get(email=username)
                    username = user_obj.username
                except User.DoesNotExist:
                    pass

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Welcome back!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


# ═══════════════════════════════════════════════════
#  DASHBOARD VIEWS
# ═══════════════════════════════════════════════════

@login_required
def dashboard(request):
    """Role-based dashboard redirect."""
    role = request.user.profile.role
    if role == 'donor':
        return donor_dashboard(request)
    elif role == 'charity':
        return charity_dashboard(request)
    elif role == 'admin':
        return admin_dashboard(request)
    return redirect('landing')


def donor_dashboard(request):
    """Donor dashboard with listings and stats."""
    listings = FoodListing.objects.filter(donor=request.user)
    active = listings.filter(status='available')
    matched = listings.filter(status='matched')
    verified = listings.filter(status='verified')

    stats = {
        'total_listings': listings.count(),
        'active_count': active.count(),
        'matched_count': matched.count(),
        'verified_count': verified.count(),
        'total_kg': listings.filter(status='verified').aggregate(s=Sum('quantity_kg'))['s'] or 0,
        'total_value': listings.filter(status='verified').aggregate(s=Sum('estimated_value'))['s'] or 0,
    }

    return render(request, 'core/dashboard_donor.html', {
        'listings': listings[:10],
        'stats': stats,
    })


def charity_dashboard(request):
    """Charity dashboard with matches and demand forecast."""
    matches = Match.objects.filter(charity=request.user).select_related('listing', 'listing__donor', 'listing__donor__profile')
    pending = matches.filter(status='pending')
    accepted = matches.filter(status='accepted')
    verified = matches.filter(status='verified')

    stats = {
        'pending_count': pending.count(),
        'accepted_count': accepted.count(),
        'verified_count': verified.count(),
        'total_received_kg': verified.aggregate(
            s=Sum('listing__quantity_kg'))['s'] or 0,
    }

    # Demand forecast
    from .services.ml_forecast import get_demand_forecast
    forecast = get_demand_forecast(request.user, periods=7)

    return render(request, 'core/dashboard_charity.html', {
        'matches': matches[:10],
        'pending_matches': pending,
        'accepted_matches': accepted,
        'stats': stats,
        'forecast': json.dumps(forecast),
    })


def admin_dashboard(request):
    """Admin overview dashboard."""
    metrics = ImpactMetrics.get_metrics()

    recent_listings = FoodListing.objects.select_related('donor__profile').all()[:10]
    recent_matches = Match.objects.all().select_related('listing', 'listing__donor__profile', 'charity__profile')[:10]

    users_by_role = UserProfile.objects.values('role').annotate(count=Count('id'))

    return render(request, 'core/dashboard_admin.html', {
        'metrics': metrics,
        'recent_listings': recent_listings,
        'recent_matches': recent_matches,
        'users_by_role': {item['role']: item['count'] for item in users_by_role},
    })


# ═══════════════════════════════════════════════════
#  FOOD LISTING VIEWS
# ═══════════════════════════════════════════════════

@login_required
@donor_required
def create_listing(request):
    """Create a new food surplus listing and immediately trigger AI matching."""
    if request.method == 'POST':
        form = FoodListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.donor = request.user
            listing.save()

            # ── Trigger AI matching ──────────────────────────
            match = None
            try:
                from .services.matching_engine import find_best_match
                match = find_best_match(listing)
            except Exception as e:
                logger.error(f"Matching engine error: {e}")

            if match:
                # ── Generate pickup QR code ──────────────────
                try:
                    from .services.qr_service import generate_pickup_qr
                    generate_pickup_qr(match)
                except Exception as e:
                    logger.error(f"QR generation error: {e}")

                # ── Send match notifications ─────────────────
                try:
                    from .services.email_service import notify_match_created
                    notify_match_created(match)
                except Exception as e:
                    logger.error(f"Email notification error: {e}")

                messages.success(
                    request,
                    f"✅ Listing created and matched with "
                    f"{match.charity.profile.organization_name} "
                    f"({match.road_distance_km:.1f} km away, "
                    f"score: {round(match.match_score * 100, 1)}%)!"
                )
            else:
                messages.success(request, "📦 Listing created! We'll find a match soon.")

            return redirect('dashboard')
    else:
        form = FoodListingForm()

    return render(request, 'core/create_listing.html', {'form': form})


@login_required
def listing_detail(request, listing_id):
    """View listing details with all associated matches."""
    listing = get_object_or_404(FoodListing, id=listing_id)

    # Only the donor or an admin can view
    if request.user != listing.donor and request.user.profile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    matches = listing.matches.all().select_related('charity__profile')

    return render(request, 'core/listing_detail.html', {
        'listing': listing,
        'matches': matches,
    })


# ═══════════════════════════════════════════════════
#  MATCH WORKFLOW VIEWS
# ═══════════════════════════════════════════════════

@login_required
@charity_required
def accept_match(request, match_id):
    """Charity accepts a pending match."""
    match = get_object_or_404(Match, id=match_id, charity=request.user, status='pending')
    match.status = 'accepted'
    match.accepted_at = timezone.now()
    match.save()

    # ── Generate (or regenerate) pickup QR ──────────────
    try:
        from .services.qr_service import generate_pickup_qr
        generate_pickup_qr(match)
    except Exception as e:
        logger.error(f"QR generation error on accept: {e}")

    # ── Notify donor ──────────────────────────────────────
    try:
        from .services.email_service import notify_match_accepted
        notify_match_accepted(match)
    except Exception as e:
        logger.error(f"Email error on accept: {e}")

    messages.success(request, '✅ Match accepted! A unique QR code has been generated for pickup.')
    return redirect('dashboard')


@login_required
@charity_required
def reject_match(request, match_id):
    """Charity rejects a pending match."""
    match = get_object_or_404(Match, id=match_id, charity=request.user, status='pending')
    match.status = 'rejected'
    match.save()

    # Re-run matching for the listing
    listing = match.listing
    listing.status = 'available'
    listing.save()

    try:
        from .services.matching_engine import find_best_match
        new_match = find_best_match(listing)
        if new_match:
            from .services.qr_service import generate_pickup_qr
            generate_pickup_qr(new_match)
            from .services.email_service import notify_match_created
            notify_match_created(new_match)
    except Exception as e:
        logger.error(f"Re-matching error: {e}")

    messages.info(request, "Match declined. We'll find another charity.")
    return redirect('dashboard')


@login_required
def confirm_pickup(request, match_id):
    """Mark a match as picked up."""
    match = get_object_or_404(Match, id=match_id, status='accepted')

    # Only the charity or donor involved can confirm
    if request.user != match.charity and request.user != match.listing.donor:
        messages.error(request, 'Unauthorized.')
        return redirect('dashboard')

    if request.method == 'POST':
        # Verify QR Code
        qr_data = request.POST.get('qr_data', '')
        if f'Match: {match.id}' not in qr_data:
            messages.error(request, 'Invalid QR code. Match ID does not correspond to this match.')
            return redirect('confirm_pickup', match_id=match.id)

        match.status = 'picked_up'
        match.picked_up_at = timezone.now()
        match.listing.status = 'picked_up'
        match.listing.save()
        match.save()

        messages.success(request, '🚚 Pickup confirmed with QR verification!')
        return redirect('dashboard')
        
    return render(request, 'core/confirm_pickup.html', {'match': match})


@login_required
def verify_delivery(request, match_id):
    """Upload delivery photo and trigger blockchain verification."""
    match = get_object_or_404(Match, id=match_id, status='picked_up')

    if request.user != match.charity and request.user != match.listing.donor:
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            messages.error(request, 'Unauthorized.')
            return redirect('dashboard')

    if request.method == 'POST':
        # Verify QR Code
        qr_data = request.POST.get('qr_data', '')
        if f'Match: {match.id}' not in qr_data:
            messages.error(request, 'Invalid QR code. Match ID does not correspond to this match.')
            return redirect('verify_delivery', match_id=match.id)

        form = DeliveryPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            match.delivery_photo = form.cleaned_data['photo']

            # ── Blockchain verification ──────────────────────
            tx_hash = None
            try:
                from .services.blockchain_service import record_verification
                tx_hash = record_verification(match)
                match.blockchain_tx_hash = tx_hash or ''
            except Exception as e:
                logger.error(f"Blockchain error: {e}")
                match.blockchain_tx_hash = ''

            match.status = 'verified'
            match.verified_at = timezone.now()
            match.listing.status = 'verified'
            match.listing.save()
            match.save()

            # ── Update impact metrics ────────────────────────
            try:
                metrics = ImpactMetrics.get_metrics()
                metrics.total_kg_saved += match.listing.quantity_kg
                metrics.total_value_saved += match.listing.estimated_value
                metrics.total_verifications += 1
                metrics.total_matches += 1
                metrics.save()
            except Exception as e:
                logger.error(f"Metrics update error: {e}")

            # ── Record demand history ────────────────────────
            try:
                DemandHistory.objects.create(
                    charity=match.charity,
                    food_type=match.listing.food_type,
                    quantity_kg=match.listing.quantity_kg,
                )
            except Exception as e:
                logger.error(f"Demand history error: {e}")

            # ── Send verification notification ───────────────
            try:
                from .services.email_service import notify_verification_complete
                notify_verification_complete(match)
            except Exception as e:
                logger.error(f"Verification email error: {e}")

            tx_display = (tx_hash[:20] + '...') if tx_hash and len(tx_hash) > 20 else (tx_hash or 'mock')
            messages.success(request, f'🔗 Delivery verified on blockchain! TX: {tx_display}')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please upload a valid photo.')
    else:
        form = DeliveryPhotoForm()

    return render(request, 'core/verify_delivery.html', {
        'match': match,
        'form': form,
    })


# ═══════════════════════════════════════════════════
#  QR CODE VIEW
# ═══════════════════════════════════════════════════

@login_required
def match_qr(request, match_id):
    """
    Display (or regenerate) the pickup QR code for a match.
    Accessible by the donor, charity, or admin.
    """
    match = get_object_or_404(Match, id=match_id)

    # Access control
    is_donor   = request.user == match.listing.donor
    is_charity = request.user == match.charity
    is_admin   = hasattr(request.user, 'profile') and request.user.profile.role == 'admin'

    if not (is_donor or is_charity or is_admin):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    # Generate QR if not already present
    if not match.qr_code:
        try:
            from .services.qr_service import generate_pickup_qr
            generate_pickup_qr(match)
            match.refresh_from_db()
        except Exception as e:
            logger.error(f"QR view generation error: {e}")

    return render(request, 'core/match_qr.html', {'match': match})


# ═══════════════════════════════════════════════════
#  DIGITAL RECEIPT VIEW
# ═══════════════════════════════════════════════════

@login_required
def download_receipt(request, match_id):
    """
    Generate and stream a PDF receipt for a verified donation match.
    Only accessible after verification is complete.
    """
    match = get_object_or_404(Match, id=match_id, status='verified')

    # Access control
    is_donor   = request.user == match.listing.donor
    is_charity = request.user == match.charity
    is_admin   = hasattr(request.user, 'profile') and request.user.profile.role == 'admin'

    if not (is_donor or is_charity or is_admin):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    try:
        from .services.receipt_service import generate_receipt_pdf
        pdf_bytes = generate_receipt_pdf(match)

        if pdf_bytes:
            filename = f"FoodWasteChain_Receipt_{str(match.id)[:8].upper()}.pdf"
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(pdf_bytes)
            response.write(pdf_bytes)
            return response
        else:
            messages.error(request, 'Could not generate receipt. Please try again.')
            return redirect('dashboard')

    except Exception as e:
        logger.error(f"Receipt download error: {e}")
        messages.error(request, 'Receipt generation failed.')
        return redirect('dashboard')


# ═══════════════════════════════════════════════════
#  API / AJAX ENDPOINTS
# ═══════════════════════════════════════════════════

@login_required
def api_listings(request):
    """JSON API for available listings (used by map views)."""
    listings = FoodListing.objects.filter(status='available').select_related('donor__profile')
    data = []
    for listing in listings:
        data.append({
            'id': str(listing.id),
            'food_type': listing.get_food_type_display(),
            'quantity_kg': float(listing.quantity_kg),
            'donor': listing.donor.profile.organization_name,
            'lat': listing.donor.profile.latitude,
            'lng': listing.donor.profile.longitude,
            'time_remaining': listing.time_remaining,
            'created': listing.created_at.isoformat(),
        })
    return JsonResponse({'listings': data})


@login_required
def api_impact(request):
    """JSON API for platform impact metrics."""
    m = ImpactMetrics.get_metrics()
    return JsonResponse({
        'total_kg_saved': float(m.total_kg_saved),
        'total_value_saved': float(m.total_value_saved),
        'total_verifications': m.total_verifications,
        'total_matches': m.total_matches,
        'total_donors': m.total_donors,
        'total_charities': m.total_charities,
    })


@login_required
def api_match_detail(request, match_id):
    """JSON API for match details (includes blockchain and geo data)."""
    match = get_object_or_404(Match, id=match_id)

    is_donor   = request.user == match.listing.donor
    is_charity = request.user == match.charity
    is_admin   = hasattr(request.user, 'profile') and request.user.profile.role == 'admin'

    if not (is_donor or is_charity or is_admin):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    return JsonResponse({
        'id': str(match.id),
        'listing': {
            'food_type': match.listing.get_food_type_display(),
            'quantity_kg': float(match.listing.quantity_kg),
            'donor':       match.listing.donor.profile.organization_name,
            'donor_lat':   match.listing.donor.profile.latitude,
            'donor_lng':   match.listing.donor.profile.longitude,
        },
        'charity': match.charity.profile.organization_name,
        'charity_lat': match.charity.profile.latitude,
        'charity_lng': match.charity.profile.longitude,
        'match_score':     float(match.match_score),
        'need_score':      float(match.need_score),
        'distance_km':     float(match.distance_km),
        'road_distance_km': float(match.road_distance_km),
        'status':          match.status,
        'blockchain_tx':   match.blockchain_tx_hash,
        'etherscan_url':   match.etherscan_url,
        'qr_code_url':     match.qr_code.url if match.qr_code else None,
    })
