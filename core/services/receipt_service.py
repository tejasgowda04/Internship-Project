"""
Digital Receipt (PDF) Service
Generates a branded PDF receipt for each verified food donation.
Zero-cost: uses reportlab (pure Python, no external services).
"""
import io
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_receipt_pdf(match):
    """
    Generate a PDF receipt for a verified donation match.
    Returns raw PDF bytes or None on failure.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table,
            TableStyle, HRFlowable, Image as RLImage
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        # ── Colour palette ─────────────────────────────────
        EMERALD = colors.HexColor('#10b981')
        DARK    = colors.HexColor('#0a0f1a')
        LIGHT   = colors.HexColor('#f9fafb')
        MUTED   = colors.HexColor('#6b7280')
        SKY     = colors.HexColor('#0ea5e9')
        BORDER  = colors.HexColor('#1e2a3a')

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=EMERALD,
            spaceAfter=4,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
        )
        sub_style = ParagraphStyle(
            'Sub',
            parent=styles['Normal'],
            fontSize=9,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=0,
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Normal'],
            fontSize=11,
            textColor=DARK,
            fontName='Helvetica-Bold',
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#111827'),
            spaceAfter=4,
        )
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=9,
            textColor=MUTED,
        )
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=MUTED,
            alignment=TA_CENTER,
        )
        chain_style = ParagraphStyle(
            'Chain',
            parent=styles['Normal'],
            fontSize=8,
            textColor=SKY,
            fontName='Helvetica',
            wordWrap='CJK',
        )

        elements = []

        # ── Header ─────────────────────────────────────────
        elements.append(Paragraph("🌿 FoodWasteChain", title_style))
        elements.append(Paragraph("Official Donation & Delivery Receipt", sub_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=2, color=EMERALD, spaceAfter=16))

        # Receipt meta
        issued_at = timezone.now().strftime('%d %B %Y, %I:%M %p IST')
        match_id_short = str(match.id).upper()[:8]
        meta_data = [
            ['Receipt No.', f'FWC-{match_id_short}'],
            ['Issued On',   issued_at],
            ['Status',      '✅ VERIFIED ON BLOCKCHAIN'],
        ]
        meta_table = Table(meta_data, colWidths=[4 * cm, 12 * cm])
        meta_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
            ('TEXTCOLOR', (1, 0), (1, -1), DARK),
            ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1, 2), (1, 2), EMERALD),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 16))

        # ── Parties ─────────────────────────────────────────
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=12))

        donor_org  = match.listing.donor.profile.organization_name or match.listing.donor.username
        donor_addr = match.listing.donor.profile.address or 'N/A'
        donor_ph   = match.listing.donor.profile.phone or 'N/A'
        charity_org  = match.charity.profile.organization_name or match.charity.username
        charity_addr = match.charity.profile.address or 'N/A'
        charity_ph   = match.charity.profile.phone or 'N/A'

        parties_data = [
            [
                Paragraph('<b>DONOR</b>', heading_style),
                Paragraph('<b>CHARITY</b>', heading_style),
            ],
            [
                Paragraph(donor_org, body_style),
                Paragraph(charity_org, body_style),
            ],
            [
                Paragraph(donor_addr, label_style),
                Paragraph(charity_addr, label_style),
            ],
            [
                Paragraph(f'Ph: {donor_ph}', label_style),
                Paragraph(f'Ph: {charity_ph}', label_style),
            ],
        ]
        parties_table = Table(parties_data, colWidths=[8 * cm, 8 * cm])
        parties_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, BORDER),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0fdf4')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT, colors.white]),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 16))

        # ── Food Details ─────────────────────────────────────
        elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=12))
        elements.append(Paragraph("Donation Details", heading_style))

        food_data = [
            ['Food Type',          match.listing.get_food_type_display()],
            ['Quantity',           f'{match.listing.quantity_kg} kg'],
            ['Estimated Value',    f'\u20b9 {match.listing.estimated_value}'],
            ['Description',        match.listing.description or '—'],
            ['Expiry Time',        match.listing.expiry_time.strftime('%d %b %Y, %I:%M %p')],
        ]
        food_table = Table(food_data, colWidths=[5 * cm, 11 * cm])
        food_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1, 0), (1, -1), DARK),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [LIGHT, colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.25, BORDER),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(food_table)
        elements.append(Spacer(1, 16))

        # ── Match Metrics ─────────────────────────────────────
        elements.append(Paragraph("Matching Metrics", heading_style))
        metrics_data = [
            ['Match Score',        f'{round(float(match.match_score) * 100, 1)}%'],
            ['Road Distance',      f'{match.road_distance_km:.1f} km'],
            ['Haversine Distance', f'{match.distance_km:.1f} km'],
            ['Need Score',         f'{round(float(match.need_score) * 100, 1)}%'],
        ]
        metrics_table = Table(metrics_data, colWidths=[5 * cm, 11 * cm])
        metrics_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1, 0), (1, -1), EMERALD),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [LIGHT, colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.25, BORDER),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 16))

        # ── Timeline ─────────────────────────────────────────
        elements.append(Paragraph("Delivery Timeline", heading_style))
        timeline_data = [
            ['Event', 'Timestamp'],
            ['Match Created',    match.created_at.strftime('%d %b %Y, %I:%M %p')],
            ['Accepted By Charity', match.accepted_at.strftime('%d %b %Y, %I:%M %p') if match.accepted_at else '—'],
            ['Picked Up',        match.picked_up_at.strftime('%d %b %Y, %I:%M %p') if match.picked_up_at else '—'],
            ['Verified & Recorded', match.verified_at.strftime('%d %b %Y, %I:%M %p') if match.verified_at else '—'],
        ]
        tl_table = Table(timeline_data, colWidths=[7 * cm, 9 * cm])
        tl_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, 0), (-1, 0), DARK),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT, colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.25, BORDER),
            ('TEXTCOLOR', (0, 4), (-1, 4), EMERALD),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(tl_table)
        elements.append(Spacer(1, 20))

        # ── Blockchain Proof ──────────────────────────────────
        elements.append(HRFlowable(width="100%", thickness=0.5, color=SKY, spaceAfter=12))
        elements.append(Paragraph("⛓ Blockchain Verification", heading_style))

        tx_hash = match.blockchain_tx_hash or 'N/A'
        etherscan = match.etherscan_url or 'N/A'

        bc_data = [
            ['Transaction Hash', tx_hash],
            ['Etherscan URL',    etherscan],
            ['Network',         'Ethereum Sepolia Testnet (Chain ID: 11155111)'],
        ]
        bc_table = Table(bc_data, colWidths=[4 * cm, 12 * cm])
        bc_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
            ('TEXTCOLOR', (1, 0), (1, -1), SKY),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f0f9ff'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.25, BORDER),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('WORDWRAP', (1, 0), (1, -1), True),
        ]))
        elements.append(bc_table)
        elements.append(Spacer(1, 16))

        # ── QR Code ───────────────────────────────────────────
        from core.services.qr_service import generate_pickup_qr_bytes
        qr_bytes = generate_pickup_qr_bytes(match)
        if qr_bytes:
            qr_buffer = io.BytesIO(qr_bytes)
            qr_img = RLImage(qr_buffer, width=3 * cm, height=3 * cm)
            qr_row = Table([[qr_img, Paragraph(
                '<b>Pickup QR Code</b><br/>'
                '<font size="8" color="#6b7280">Scan this unique QR at time of pickup '
                'to verify the transaction is authentic.</font>',
                body_style
            )]], colWidths=[4 * cm, 12 * cm])
            qr_row.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(qr_row)
            elements.append(Spacer(1, 16))

        # ── Footer ──────────────────────────────────────────
        elements.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=8))
        elements.append(Paragraph(
            "This receipt is auto-generated by the FoodWasteChain platform. "
            "The blockchain transaction hash serves as an immutable proof of delivery. "
            "For disputes, contact support@foodwastechain.org",
            footer_style
        ))
        elements.append(Paragraph(
            f"© FoodWasteChain {timezone.now().year} — Zero-Cost Food Redistribution | Powered by Ethereum",
            footer_style
        ))

        # Build PDF
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    except Exception as e:
        logger.error(f"Receipt PDF generation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
