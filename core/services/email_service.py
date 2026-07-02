"""
Email Notification Service
Sends automated notifications for matches, verifications, and alerts.
"""
import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)


def notify_match_created(match):
    """Notify both donor and charity about a new match."""
    try:
        # Base context that is generally useful
        base_context = {
            'food_type': match.listing.get_food_type_display(),
            'quantity': match.listing.quantity_kg,
            'donor_name': match.listing.donor.profile.organization_name,
            'charity_name': match.charity.profile.organization_name,
            'distance': round(match.road_distance_km, 1),
            'expiry': timezone.localtime(match.listing.expiry_time).strftime('%d %b %Y, %I:%M %p'),
            'match_score': round(float(match.match_score) * 100, 1) if match.match_score else 0,
            # For the dashboard link we might just use the absolute domain if available, but a relative is okay if the user visits the app on local
            'dashboard_url': settings.SITE_URL + '/dashboard' if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000/dashboard'
        }

        # --- Notify the charity ---
        charity_subject = f"🍽️ New Food Match Available — {match.listing.get_food_type_display()}"
        charity_text = (
            f"Hi {match.charity.first_name or match.charity.username},\n\n"
            f"A new food donation has been matched to your organization.\n"
            f"Please log in to FoodWasteChain to accept or decline this match.\n\n"
            f"— FoodWasteChain Team"
        )
        charity_html = render_to_string('core/emails/match_created_charity.html', base_context)

        send_mail(
            subject=charity_subject,
            message=charity_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[match.charity.email],
            html_message=charity_html,
            fail_silently=True,
        )

        # --- Notify the donor ---
        donor_subject = f"✅ Match Found — {match.listing.get_food_type_display()}"
        donor_text = (
            f"Hi {match.listing.donor.first_name or match.listing.donor.username},\n\n"
            f"Your food listing has been matched with a nearby charity!\n"
            f"The charity has been notified and will confirm pickup soon.\n\n"
            f"— FoodWasteChain Team"
        )
        donor_html = render_to_string('core/emails/match_created_donor.html', base_context)

        send_mail(
            subject=donor_subject,
            message=donor_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[match.listing.donor.email],
            html_message=donor_html,
            fail_silently=True,
        )

        logger.info(f"Match notification sent for match {match.id}")

    except Exception as e:
        logger.error(f"Email notification failed: {e}")


def notify_verification_complete(match):
    """Notify both parties that verification is complete."""
    try:
        etherscan_url = match.etherscan_url or "Not available"
        tx_hash = match.blockchain_tx_hash or "Pending"

        context = {
            'food_type': match.listing.get_food_type_display(),
            'quantity': match.listing.quantity_kg,
            'donor_name': match.listing.donor.profile.organization_name,
            'charity_name': match.charity.profile.organization_name,
            'etherscan_url': etherscan_url,
            'tx_hash': tx_hash,
            'dashboard_url': settings.SITE_URL + '/dashboard' if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000/dashboard'
        }

        subject = f"🔗 Donation Verified on Blockchain — {match.listing.get_food_type_display()}"
        text_content = (
            f"Congratulations! Your food donation has been verified and recorded.\n\n"
            f"Thank you for making a difference!\n\n"
            f"— FoodWasteChain Team"
        )
        html_content = render_to_string('core/emails/verification_complete.html', context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[match.listing.donor.email, match.charity.email],
        )
        msg.attach_alternative(html_content, "text/html")

        try:
            from .receipt_service import generate_receipt_pdf
            pdf_bytes = generate_receipt_pdf(match)
            if pdf_bytes:
                filename = f"FoodWasteChain_Receipt_{str(match.id)[:8].upper()}.pdf"
                msg.attach(filename, pdf_bytes, 'application/pdf')
        except Exception as pdf_err:
            logger.error(f"Failed to attach receipt PDF: {pdf_err}")

        msg.send(fail_silently=True)

        logger.info(f"Verification notification sent for match {match.id}")

    except Exception as e:
        logger.error(f"Verification email failed: {e}")


def notify_match_accepted(match):
    """Notify donor that charity accepted the match."""
    try:
        context = {
            'donor_name': match.listing.donor.first_name or match.listing.donor.username,
            'charity_name': match.charity.profile.organization_name,
            'food_type': match.listing.get_food_type_display(),
            'quantity': match.listing.quantity_kg,
            'dashboard_url': settings.SITE_URL + '/dashboard' if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000/dashboard'
        }

        subject = f"🎉 Match Accepted — Pickup Scheduled"
        text_content = (
            f"Hi {context['donor_name']},\n\n"
            f"{context['charity_name']} has accepted the food match!\n"
            f"Please prepare the food for pickup.\n\n"
            f"— FoodWasteChain Team"
        )
        html_content = render_to_string('core/emails/match_accepted.html', context)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[match.listing.donor.email],
            html_message=html_content,
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Accepted email failed: {e}")


def notify_registration_approved(profile):
    """Notify a charity that their registration has been approved."""
    try:
        user = profile.user
        subject = "✅ Registration Approved — Welcome to FoodWasteChain!"
        text_content = (
            f"Hi {profile.organization_name},\n\n"
            f"Great news! Your registration on FoodWasteChain has been approved.\n\n"
            f"You can now log in with your credentials and start receiving food donations.\n\n"
            f"Login here: http://127.0.0.1:8000/login/\n"
            f"Username: {user.username}\n\n"
            f"— FoodWasteChain Admin Team"
        )

        html_content = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto;
                    background: #0a0f1a; color: #f9fafb; padding: 40px; border-radius: 16px;">
            <div style="text-align: center; margin-bottom: 32px;">
                <span style="font-size: 2rem;">🌿</span>
                <h1 style="background: linear-gradient(135deg, #10b981, #0ea5e9);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                           font-size: 1.5rem; margin: 8px 0;">FoodWasteChain</h1>
            </div>
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3);
                        border-radius: 12px; padding: 24px; margin-bottom: 24px;">
                <h2 style="color: #34d399; margin: 0 0 8px;">✅ Registration Approved!</h2>
                <p style="color: #9ca3af; margin: 0;">Your organization has been verified and approved.</p>
            </div>
            <p style="color: #d1d5db; line-height: 1.6;">
                Hi <strong>{profile.organization_name}</strong>,<br><br>
                Your registration has been reviewed and approved by our admin team.
                You can now log in and start receiving food donation matches!
            </p>
            <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 12px; padding: 20px; margin: 24px 0;">
                <p style="color: #9ca3af; margin: 0 0 8px; font-size: 0.85rem;">YOUR LOGIN DETAILS</p>
                <p style="color: #f9fafb; margin: 0;"><strong>Username:</strong> {user.username}</p>
                <p style="color: #f9fafb; margin: 0;"><strong>Email:</strong> {user.email}</p>
            </div>
            <div style="text-align: center; margin-top: 32px;">
                <a href="http://127.0.0.1:8000/login/"
                   style="background: linear-gradient(135deg, #10b981, #0ea5e9); color: #fff;
                          padding: 14px 32px; border-radius: 12px; text-decoration: none;
                          font-weight: 600; display: inline-block;">
                    Log In Now →
                </a>
            </div>
            <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 32px 0;">
            <p style="color: #6b7280; font-size: 0.8rem; text-align: center;">
                © 2026 FoodWasteChain — Zero-Cost Food Redistribution
            </p>
        </div>
        """

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=True,
        )

        logger.info(f"Approval notification sent to {user.email}")

    except Exception as e:
        logger.error(f"Registration approval email failed: {e}")


def notify_registration_rejected(profile):
    """Notify a charity that their registration has been rejected."""
    try:
        user = profile.user
        subject = "❌ Registration Update — FoodWasteChain"
        text_content = (
            f"Hi {profile.organization_name},\n\n"
            f"Unfortunately, your registration on FoodWasteChain has not been approved at this time.\n\n"
            f"Reason: {profile.admin_notes}\n\n"
            f"If you believe this is an error, please contact our support team.\n\n"
            f"— FoodWasteChain Admin Team"
        )

        html_content = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto;
                    background: #0a0f1a; color: #f9fafb; padding: 40px; border-radius: 16px;">
            <div style="text-align: center; margin-bottom: 32px;">
                <span style="font-size: 2rem;">🌿</span>
                <h1 style="background: linear-gradient(135deg, #10b981, #0ea5e9);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                           font-size: 1.5rem; margin: 8px 0;">FoodWasteChain</h1>
            </div>
            <div style="background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3);
                        border-radius: 12px; padding: 24px; margin-bottom: 24px;">
                <h2 style="color: #fb7185; margin: 0 0 8px;">Registration Not Approved</h2>
                <p style="color: #9ca3af; margin: 0;">Please review the details below.</p>
            </div>
            <p style="color: #d1d5db; line-height: 1.6;">
                Hi <strong>{profile.organization_name}</strong>,<br><br>
                After reviewing your registration, our admin team was unable to approve it at this time.
            </p>
            <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 12px; padding: 20px; margin: 24px 0;">
                <p style="color: #9ca3af; margin: 0 0 8px; font-size: 0.85rem;">REASON</p>
                <p style="color: #f9fafb; margin: 0;">{profile.admin_notes}</p>
            </div>
            <p style="color: #9ca3af; line-height: 1.6; font-size: 0.9rem;">
                If you believe this is an error or would like to provide additional documentation,
                please contact our support team.
            </p>
            <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 32px 0;">
            <p style="color: #6b7280; font-size: 0.8rem; text-align: center;">
                © 2026 FoodWasteChain — Zero-Cost Food Redistribution
            </p>
        </div>
        """

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=True,
        )

        logger.info(f"Rejection notification sent to {user.email}")

    except Exception as e:
        logger.error(f"Registration rejection email failed: {e}")

