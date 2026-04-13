"""
QR Code Generation Service
Generates a unique QR code for each match pickup event.
The QR encodes a signed verification token (match ID + timestamp + hash).
"""
import io
import os
import hashlib
import logging
from django.core.files.base import ContentFile
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_pickup_qr(match):
    """
    Generate a unique QR code for a match pickup.
    The QR contains a signed JSON payload with match details.
    Saves the image to match.qr_code field and returns True on success.
    """
    try:
        import qrcode
        from qrcode.image.styledpil import StyledPilImage
        from qrcode.image.styles.moduledrawers import RoundedModuleDrawer

        # Build a unique, tamper-evident payload
        timestamp = timezone.now().isoformat()
        secret = os.environ.get('SECRET_KEY', 'foodwastechain-secret')
        raw = f"{match.id}|{match.listing.id}|{match.charity.username}|{timestamp}"
        sig = hashlib.sha256(f"{raw}{secret}".encode()).hexdigest()[:16]

        payload = (
            f"FOODWASTECHAIN-PICKUP\n"
            f"Match: {match.id}\n"
            f"Food: {match.listing.get_food_type_display()}\n"
            f"Qty: {match.listing.quantity_kg} kg\n"
            f"Donor: {match.listing.donor.profile.organization_name}\n"
            f"Charity: {match.charity.profile.organization_name}\n"
            f"Issued: {timestamp}\n"
            f"Sig: {sig}"
        )

        # Generate styled QR code
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=3,
        )
        qr.add_data(payload)
        qr.make(fit=True)

        # Try styled (rounded) modules, fall back to plain
        try:
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
            )
        except Exception:
            img = qr.make_image(fill_color="black", back_color="white")

        # Save to in-memory buffer then to model field
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        filename = f"qr_{match.id}.png"
        match.qr_code.save(filename, ContentFile(buffer.read()), save=True)

        logger.info(f"QR code generated for match {match.id}")
        return True

    except ImportError as e:
        logger.error(f"qrcode library not installed: {e}")
        return False
    except Exception as e:
        logger.error(f"QR generation failed for match {match.id}: {e}")
        return False


def generate_pickup_qr_bytes(match):
    """
    Return raw PNG bytes of a QR code for use in PDF receipt generation.
    Does not save to model field.
    """
    try:
        import qrcode

        timestamp = timezone.now().isoformat()
        secret = os.environ.get('SECRET_KEY', 'foodwastechain-secret')
        raw = f"{match.id}|{match.listing.id}|{match.charity.username}|{timestamp}"
        sig = hashlib.sha256(f"{raw}{secret}".encode()).hexdigest()[:16]

        payload = (
            f"FOODWASTECHAIN-PICKUP | Match:{match.id} | "
            f"Food:{match.listing.get_food_type_display()} | "
            f"Qty:{match.listing.quantity_kg}kg | Sig:{sig}"
        )

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=3)
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"QR bytes generation failed: {e}")
        return None
