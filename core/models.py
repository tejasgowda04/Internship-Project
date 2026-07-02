import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with role-based access and geolocation."""
    ROLE_CHOICES = [
        ('donor', 'Donor'),
        ('charity', 'Charity'),
        ('admin', 'Admin'),
    ]

    APPROVAL_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='donor')
    organization_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    latitude = models.FloatField(default=12.9716)   # Default: Bangalore
    longitude = models.FloatField(default=77.5946)
    address = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

    # Registration approval workflow
    approval_status = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text='Internal notes from admin review')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_profiles')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    registration_doc = models.FileField(upload_to='registration_docs/', blank=True, null=True, help_text='Legal/license document for verification')

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_approved(self):
        """Donors are auto-approved; charities/admins need explicit approval."""
        if self.role == 'donor':
            return True
        return self.approval_status == 'approved'

    def __str__(self):
        return f"{self.organization_name or self.user.username} ({self.get_role_display()})"

    class Meta:
        ordering = ['-created_at']


class FoodListing(models.Model):
    """Food surplus listings created by donors."""
    FOOD_TYPE_CHOICES = [
        ('cooked_meals', 'Cooked Meals'),
        ('raw_vegetables', 'Raw Vegetables'),
        ('fruits', 'Fruits'),
        ('dairy', 'Dairy Products'),
        ('bakery', 'Bakery Items'),
        ('packaged', 'Packaged Food'),
        ('beverages', 'Beverages'),
        ('mixed', 'Mixed / Other'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('matched', 'Matched'),
        ('picked_up', 'Picked Up'),
        ('verified', 'Verified'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    donor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    food_type = models.CharField(max_length=20, choices=FOOD_TYPE_CHOICES)
    description = models.TextField(blank=True)
    quantity_kg = models.DecimalField(max_digits=8, decimal_places=2)
    estimated_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expiry_time = models.DateTimeField()
    photo = models.ImageField(upload_to='listings/', blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_food_type_display()} — {self.quantity_kg}kg by {self.donor.username}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expiry_time

    @property
    def time_remaining(self):
        delta = self.expiry_time - timezone.now()
        if delta.total_seconds() <= 0:
            return "Expired"
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    class Meta:
        ordering = ['-created_at']


class Match(models.Model):
    """Links a food listing to a charity with matching data."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('picked_up', 'Picked Up'),
        ('verified', 'Verified'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    listing = models.ForeignKey(FoodListing, on_delete=models.CASCADE, related_name='matches')
    charity = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_matches')
    distance_km = models.FloatField(default=0, help_text='Haversine distance')
    road_distance_km = models.FloatField(default=0, help_text='OSRM road distance')
    need_score = models.FloatField(default=0, help_text='ML-predicted need score 0.0–1.0')
    match_score = models.FloatField(default=0, help_text='Composite matching score')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    blockchain_tx_hash = models.CharField(max_length=100, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    delivery_photo = models.ImageField(upload_to='delivery_photos/', blank=True, null=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Match: {self.listing} → {self.charity.username} ({self.status})"

    @property
    def etherscan_url(self):
        if self.blockchain_tx_hash:
            return f"https://sepolia.etherscan.io/tx/{self.blockchain_tx_hash}"
        return None

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Matches'


class DemandHistory(models.Model):
    """Historical demand data for ML forecasting."""
    charity = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demand_history')
    food_type = models.CharField(max_length=20, choices=FoodListing.FOOD_TYPE_CHOICES)
    quantity_kg = models.DecimalField(max_digits=8, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.charity.username} needed {self.quantity_kg}kg {self.food_type}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Demand histories'


class ImpactMetrics(models.Model):
    """Singleton model — platform-wide impact statistics."""
    total_kg_saved = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_value_saved = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_verifications = models.IntegerField(default=0)
    total_matches = models.IntegerField(default=0)
    total_donors = models.IntegerField(default=0)
    total_charities = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    @classmethod
    def get_metrics(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Impact: {self.total_kg_saved}kg saved, {self.total_matches} matches"

    class Meta:
        verbose_name_plural = 'Impact metrics'
