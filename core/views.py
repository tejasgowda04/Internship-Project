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
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
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
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            user = User.objects.create_user(
                username=cd['username'],
                email=cd['email'],
                password=cd['password'],
            )
            # Donors are auto-approved; charities need admin review
            is_donor = cd['role'] == 'donor'
            profile = UserProfile.objects.create(
                user=user,
                role=cd['role'],
                organization_name=cd['organization_name'],
                phone=cd.get('phone') or '',
                address=cd.get('address') or '',
                latitude=cd.get('latitude') or 12.9716,
                longitude=cd.get('longitude') or 77.5946,
                approval_status='approved' if is_donor else 'pending',
                registration_doc=cd.get('registration_doc') or None,
            )
            # Update impact metrics
            metrics = ImpactMetrics.get_metrics()
            if is_donor:
                metrics.total_donors += 1
                metrics.save()
                login(request, user)
                messages.success(request, f"Welcome to FoodWasteChain, {cd['organization_name']}!")
                return redirect('dashboard')
            else:
                # Don't auto-login charities — they need admin approval first
                metrics.total_charities += 1
                metrics.save()
                messages.info(
                    request,
                    f"🎉 Registration submitted! Your charity \"{cd['organization_name']}\" "
                    f"is under review. You'll receive an email once approved by our admin team."
                )
                return redirect('login')
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
                # Block unapproved charities from logging in
                if hasattr(user, 'profile') and user.profile.role == 'charity':
                    if user.profile.approval_status == 'pending':
                        messages.warning(
                            request,
                            '⏳ Your registration is still under review. '
                            'You will receive an email notification once approved by our admin team.'
                        )
                        return render(request, 'core/login.html', {'form': form})
                    elif user.profile.approval_status == 'rejected':
                        messages.error(
                            request,
                            '❌ Your registration was rejected. '
                            'Please contact support for more information.'
                        )
                        return render(request, 'core/login.html', {'form': form})

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
    """Admin overview dashboard with registration review queue and analytics."""
    metrics = ImpactMetrics.get_metrics()

    # Pending registrations (charities awaiting approval)
    pending_registrations = UserProfile.objects.filter(
        approval_status='pending'
    ).select_related('user').order_by('-created_at')

    # Recently reviewed
    recently_reviewed = UserProfile.objects.filter(
        approval_status__in=['approved', 'rejected'],
        reviewed_at__isnull=False
    ).select_related('user', 'reviewed_by').order_by('-reviewed_at')[:10]

    # All registrations (for the full table)
    all_registrations = UserProfile.objects.exclude(
        role='admin'
    ).select_related('user').order_by('-created_at')[:50]

    recent_listings = FoodListing.objects.select_related('donor__profile').all()[:10]
    recent_matches = Match.objects.all().select_related('listing', 'listing__donor__profile', 'charity__profile')[:10]

    users_by_role = UserProfile.objects.values('role').annotate(count=Count('id'))

    # Analytics data for charts
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # Daily donation volume (last 30 days)
    daily_donations = (
        FoodListing.objects.filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'), total_kg=Sum('quantity_kg'))
        .order_by('date')
    )

    # Daily matches (last 30 days)
    daily_matches = (
        Match.objects.filter(created_at__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    # Blockchain transactions (verified matches with tx hash)
    blockchain_txns = Match.objects.filter(
        blockchain_tx_hash__isnull=False
    ).exclude(blockchain_tx_hash='').count()

    # Food type distribution
    food_distribution = (
        FoodListing.objects.values('food_type')
        .annotate(count=Count('id'), total_kg=Sum('quantity_kg'))
        .order_by('-count')
    )

    # Match status distribution
    match_statuses = (
        Match.objects.values('status')
        .annotate(count=Count('id'))
    )

    # Registration stats
    total_pending = pending_registrations.count()
    total_approved = UserProfile.objects.filter(approval_status='approved').count()
    total_rejected = UserProfile.objects.filter(approval_status='rejected').count()

    # System health indicators
    active_listings = FoodListing.objects.filter(status='available').count()
    expired_listings = FoodListing.objects.filter(status='expired').count()
    total_users = User.objects.count()

    # Build chart data as JSON
    chart_data = {
        'daily_donations': [
            {'date': d['date'].strftime('%Y-%m-%d'), 'count': d['count'], 'kg': float(d['total_kg'] or 0)}
            for d in daily_donations
        ],
        'daily_matches': [
            {'date': d['date'].strftime('%Y-%m-%d'), 'count': d['count']}
            for d in daily_matches
        ],
        'food_distribution': [
            {'type': dict(FoodListing.FOOD_TYPE_CHOICES).get(d['food_type'], d['food_type']),
             'count': d['count'], 'kg': float(d['total_kg'] or 0)}
            for d in food_distribution
        ],
        'match_statuses': [
            {'status': d['status'], 'count': d['count']}
            for d in match_statuses
        ],
    }

    return render(request, 'core/dashboard_admin.html', {
        'metrics': metrics,
        'pending_registrations': pending_registrations,
        'recently_reviewed': recently_reviewed,
        'all_registrations': all_registrations,
        'recent_listings': recent_listings,
        'recent_matches': recent_matches,
        'users_by_role': {item['role']: item['count'] for item in users_by_role},
        'chart_data': json.dumps(chart_data),
        'total_pending': total_pending,
        'total_approved': total_approved,
        'total_rejected': total_rejected,
        'blockchain_txns': blockchain_txns,
        'active_listings': active_listings,
        'expired_listings': expired_listings,
        'total_users': total_users,
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
    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        messages.error(request, 'Match not found.')
        return redirect('dashboard')

    # Security: Ensure this match belongs to the logged-in charity
    if match.charity != request.user:
        messages.error(request, 'This match is not assigned to your organization.')
        return redirect('dashboard')

    # Handle status issues
    if match.status == 'accepted':
        messages.info(request, 'This match has already been accepted.')
        return redirect('dashboard')
    
    if match.status != 'pending':
        messages.error(request, f'This match cannot be accepted because it is currently {match.get_status_display().lower()}.')
        return redirect('dashboard')

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
    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        messages.error(request, 'Match not found.')
        return redirect('dashboard')

    if match.charity != request.user:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if match.status != 'pending':
        messages.info(request, f'This match cannot be rejected as it is already {match.status}.')
        return redirect('dashboard')

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
    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        messages.error(request, 'Match not found.')
        return redirect('dashboard')

    if match.status != 'accepted':
        messages.error(request, f'Pickup cannot be confirmed. Current status: {match.get_status_display()}')
        return redirect('dashboard')

    # Only the charity or donor involved can confirm
    if request.user != match.charity and request.user != match.listing.donor:
        messages.error(request, 'Unauthorized.')
        return redirect('dashboard')

    if request.method == 'POST':
        # Verify QR Code
        qr_data = request.POST.get('qr_data', '')
        from .services.qr_service import verify_qr_data
        if not verify_qr_data(match, qr_data):
            messages.error(request, 'Invalid QR code signature or match ID does not correspond to this match.')
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
    """Upload delivery photo and trigger blockchain verification.
    Note: QR verification is NOT required here — the charity picks up
    the food at the donor's location (where QR is verified), then brings
    it back to their own location.  The donor is not present at the
    charity's site, so a delivery photo + blockchain recording is the
    appropriate proof of delivery.
    """
    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        messages.error(request, 'Match not found.')
        return redirect('dashboard')

    if match.status != 'picked_up':
        if match.status == 'verified':
            messages.info(request, 'This delivery has already been verified.')
        else:
            messages.error(request, f'Delivery cannot be verified. Current status: {match.get_status_display()}')
        return redirect('dashboard')

    if request.user != match.charity and request.user != match.listing.donor:
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            messages.error(request, 'Unauthorized.')
            return redirect('dashboard')

    if request.method == 'POST':

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
    Only accessible by the DONOR (who shows it) or admin.
    Charities must NOT see the QR — they scan it at the donor's
    location during pickup. Showing it here would allow misuse.
    """
    match = get_object_or_404(Match, id=match_id)

    # Access control — donor and admin only, NOT charity
    is_donor   = request.user == match.listing.donor
    is_admin   = hasattr(request.user, 'profile') and request.user.profile.role == 'admin'

    if not (is_donor or is_admin):
        messages.error(request, 'Access denied. Only the donor can view the QR code.')
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
    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        messages.error(request, 'Match not found.')
        return redirect('dashboard')

    if match.status != 'verified':
        messages.error(request, 'Receipt is only available for verified deliveries.')
        return redirect('dashboard')

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


# ═══════════════════════════════════════════════════
#  ADMIN REGISTRATION MANAGEMENT
# ═══════════════════════════════════════════════════

@login_required
@admin_required
def admin_registration_detail(request, profile_id):
    """View detailed info about a registration for admin review."""
    profile = get_object_or_404(UserProfile, id=profile_id)

    return render(request, 'core/admin_registration_detail.html', {
        'profile': profile,
    })


@login_required
@admin_required
@require_POST
def admin_approve_registration(request, profile_id):
    """Admin approves a pending charity registration."""
    profile = get_object_or_404(UserProfile, id=profile_id)

    if profile.approval_status != 'pending':
        messages.info(request, f'This registration has already been {profile.get_approval_status_display().lower()}.')
        return redirect('dashboard')

    admin_notes = request.POST.get('admin_notes', '')

    profile.approval_status = 'approved'
    profile.admin_notes = admin_notes
    profile.reviewed_by = request.user
    profile.reviewed_at = timezone.now()
    profile.is_verified = True
    profile.save()

    # Send approval notification email
    try:
        from .services.email_service import notify_registration_approved
        notify_registration_approved(profile)
    except Exception as e:
        logger.error(f"Approval email error: {e}")

    messages.success(
        request,
        f'✅ {profile.organization_name} has been approved! '
        f'They can now log in and use the platform.'
    )
    return redirect('dashboard')


@login_required
@admin_required
@require_POST
def admin_reject_registration(request, profile_id):
    """Admin rejects a pending charity registration."""
    profile = get_object_or_404(UserProfile, id=profile_id)

    if profile.approval_status != 'pending':
        messages.info(request, f'This registration has already been {profile.get_approval_status_display().lower()}.')
        return redirect('dashboard')

    admin_notes = request.POST.get('admin_notes', '')
    if not admin_notes:
        messages.error(request, 'Please provide a reason for rejection.')
        return redirect('admin_registration_detail', profile_id=profile.id)

    profile.approval_status = 'rejected'
    profile.admin_notes = admin_notes
    profile.reviewed_by = request.user
    profile.reviewed_at = timezone.now()
    profile.save()

    # Send rejection notification email
    try:
        from .services.email_service import notify_registration_rejected
        notify_registration_rejected(profile)
    except Exception as e:
        logger.error(f"Rejection email error: {e}")

    messages.info(
        request,
        f'❌ {profile.organization_name} registration has been rejected.'
    )
    return redirect('dashboard')

