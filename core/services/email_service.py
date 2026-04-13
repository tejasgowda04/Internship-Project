"""
Email Notification Service
Sends automated notifications for matches, verifications, and alerts.
"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def notify_match_created(match):
    """Notify both donor and charity about a new match."""
    try:
        # Notify the charity
        send_mail(
            subject=f"🍽️ New Food Match Available — {match.listing.get_food_type_display()}",
            message=(
                f"Hi {match.charity.first_name or match.charity.username},\n\n"
                f"Great news! A new food donation has been matched to your organization.\n\n"
                f"📦 Food Type: {match.listing.get_food_type_display()}\n"
                f"⚖️ Quantity: {match.listing.quantity_kg} kg\n"
                f"🏢 Donor: {match.listing.donor.profile.organization_name}\n"
                f"📍 Distance: {match.road_distance_km} km\n"
                f"⏰ Expires: {match.listing.expiry_time.strftime('%d %b %Y, %I:%M %p')}\n\n"
                f"Please log in to FoodWasteChain to accept or decline this match.\n\n"
                f"— FoodWasteChain Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[match.charity.email],
            fail_silently=True,
        )

        # Notify the donor
        send_mail(
            subject=f"✅ Match Found — {match.listing.get_food_type_display()}",
            message=(
                f"Hi {match.listing.donor.first_name or match.listing.donor.username},\n\n"
                f"Your food listing has been matched with a nearby charity!\n\n"
                f"🏠 Charity: {match.charity.profile.organization_name}\n"
                f"📍 Distance: {match.road_distance_km} km\n"
                f"📊 Match Score: {match.match_score}\n\n"
                f"The charity has been notified and will confirm pickup soon.\n\n"
                f"— FoodWasteChain Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[match.listing.donor.email],
            fail_silently=True,
        )

        logger.info(f"Match notification sent for match {match.id}")

    except Exception as e:
        logger.error(f"Email notification failed: {e}")


def notify_verification_complete(match):
    """Notify both parties that verification is complete."""
    try:
        etherscan_url = match.etherscan_url or "Not available"

        send_mail(
            subject=f"🔗 Donation Verified on Blockchain — {match.listing.get_food_type_display()}",
            message=(
                f"Congratulations! Your food donation has been verified and recorded.\n\n"
                f"📦 Food: {match.listing.get_food_type_display()} ({match.listing.quantity_kg} kg)\n"
                f"🏢 Donor: {match.listing.donor.profile.organization_name}\n"
                f"🏠 Charity: {match.charity.profile.organization_name}\n"
                f"🔗 Blockchain Proof: {etherscan_url}\n\n"
                f"Thank you for making a difference!\n\n"
                f"— FoodWasteChain Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[
                match.listing.donor.email,
                match.charity.email,
            ],
            fail_silently=True,
        )

        logger.info(f"Verification notification sent for match {match.id}")

    except Exception as e:
        logger.error(f"Verification email failed: {e}")


def notify_match_accepted(match):
    """Notify donor that charity accepted the match."""
    try:
        send_mail(
            subject=f"🎉 Match Accepted — Pickup Scheduled",
            message=(
                f"Hi {match.listing.donor.first_name or match.listing.donor.username},\n\n"
                f"{match.charity.profile.organization_name} has accepted the food match!\n\n"
                f"📦 Food: {match.listing.get_food_type_display()} ({match.listing.quantity_kg} kg)\n"
                f"Please prepare the food for pickup.\n\n"
                f"— FoodWasteChain Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[match.listing.donor.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Accepted email failed: {e}")
