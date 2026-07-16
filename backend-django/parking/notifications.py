"""Receipt generation and email delivery for confirmed parking bookings."""

import logging
from base64 import b64encode
from email.utils import parseaddr
from io import BytesIO
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone
from django.utils.html import escape
from python_http_client.exceptions import HTTPError
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sendgrid import SendGridAPIClient


logger = logging.getLogger(__name__)


def _receipt_time(value):
    if not value:
        return "Not available"
    try:
        display_zone = ZoneInfo(settings.PARKING_RECEIPT_TIME_ZONE)
        value = timezone.localtime(value, display_zone)
    except Exception:  # A bad display-zone setting must not block a receipt.
        value = timezone.localtime(value)
    return value.strftime("%d %b %Y, %I:%M %p %Z")


def _paragraph_value(value):
    return escape(str(value or "Not available"))


def _detail_cell(label, value, style):
    return Paragraph(
        f'<font color="#64748B" size="8">{escape(label.upper())}</font><br/>'
        f'<font color="#0F172A" size="10"><b>{_paragraph_value(value)}</b></font>',
        style,
    )


def build_booking_receipt(booking):
    """Return a branded, one-page PDF receipt for a confirmed booking."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Parking receipt {booking.booking_id}",
        author="Parking Reservations",
    )
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "ReceiptBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        leading=15,
        textColor=colors.HexColor("#334155"),
    )
    detail = ParagraphStyle("ReceiptDetail", parent=body, leading=14)
    title = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.white,
    )
    subtitle = ParagraphStyle(
        "ReceiptSubtitle",
        parent=body,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#BFDBFE"),
    )
    booking_meta = ParagraphStyle(
        "ReceiptMeta",
        parent=subtitle,
        alignment=TA_RIGHT,
        textColor=colors.white,
    )
    section = ParagraphStyle(
        "ReceiptSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=7,
    )
    status = ParagraphStyle(
        "ReceiptStatus",
        parent=body,
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#166534"),
        backColor=colors.HexColor("#DCFCE7"),
        borderPadding=(6, 10, 6, 10),
        borderRadius=5,
    )

    booking_created = _receipt_time(booking.created_at or booking.start_time)
    header = Table(
        [[
            Paragraph("Parking reservations", subtitle),
            Paragraph(f"Booking reference<br/><b>{_paragraph_value(booking.booking_id)}</b>", booking_meta),
        ], [
            Paragraph("Your parking is confirmed", title),
            Paragraph(f"Issued {booking_created}", booking_meta),
        ]],
        colWidths=[112 * mm, 62 * mm],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0F172A")),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (0, -1), 16),
                ("RIGHTPADDING", (-1, 0), (-1, -1), 16),
                ("LEFTPADDING", (1, 0), (1, -1), 8),
                ("RIGHTPADDING", (0, 0), (0, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )

    owner_details = Table(
        [[
            _detail_cell("Owner name", booking.owner_name, detail),
            _detail_cell("Email", booking.owner_email, detail),
        ], [
            _detail_cell("Phone", booking.owner_phone, detail),
            _detail_cell("Vehicle", f"{booking.vehicle_number} - {booking.vehicle_type.name}", detail),
        ]],
        colWidths=[87 * mm, 87 * mm],
    )
    parking_details = Table(
        [[
            _detail_cell("Parking location", booking.parking_lot.name, detail),
            _detail_cell("Allocated slot", f"{booking.slot.zone}-{booking.slot.number} (Floor {booking.slot.floor})", detail),
        ], [
            _detail_cell("Address", booking.parking_lot.address, detail),
            _detail_cell("Reservation valid until", _receipt_time(booking.reservation_expires_at), detail),
        ]],
        colWidths=[87 * mm, 87 * mm],
    )
    for table in (owner_details, parking_details):
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#E2E8F0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

    story = [
        header,
        Spacer(1, 9 * mm),
        Paragraph("CONFIRMED RESERVATION", status),
        Spacer(1, 7 * mm),
        Paragraph("Owner and vehicle", section),
        owner_details,
        Spacer(1, 7 * mm),
        Paragraph("Parking allocation", section),
        parking_details,
        Spacer(1, 8 * mm),
        HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#CBD5E1")),
        Spacer(1, 5 * mm),
        Paragraph(
            "Please arrive before the reservation expires and keep this receipt available at the entrance. "
            "For any assistance, reply to the confirmation email.",
            body,
        ),
    ]
    document.build(story)
    return output.getvalue()


def _receipt_delivery(sent, error=None):
    return {"sent": sent, "error": error}


def _sendgrid_sender(value):
    name, email = parseaddr(value or "")
    if not email:
        return None
    sender = {"email": email}
    if name:
        sender["name"] = name
    return sender


def _sendgrid_error_detail(error):
    body = getattr(error, "body", "")
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    return str(body or error).strip()[:500]


def send_booking_confirmation(booking):
    """Deliver the booking receipt through the SendGrid Web API.

    This function is called only after BookingService's atomic block has exited,
    so a delivery failure can never roll back a confirmed parking reservation.
    """
    owner_email = (booking.owner_email or "").strip().lower()
    if not owner_email:
        logger.warning("Receipt not sent for %s: owner email is missing", booking.booking_id)
        return _receipt_delivery(False, "Owner email is missing.")

    if not settings.SENDGRID_API_KEY:
        logger.error("Receipt not sent for %s: SENDGRID_API_KEY is not configured", booking.booking_id)
        return _receipt_delivery(False, "SendGrid is not configured.")

    sender = _sendgrid_sender(settings.DEFAULT_FROM_EMAIL)
    if not sender:
        logger.error("Receipt not sent for %s: DEFAULT_FROM_EMAIL is invalid", booking.booking_id)
        return _receipt_delivery(False, "The sender email configuration is invalid.")

    developer_email = (settings.PARKING_DEVELOPER_EMAIL or "").strip().lower()
    subject = f"Parking confirmed - {booking.booking_id}"
    text_body = (
        f"Hi {booking.owner_name},\n\n"
        f"Your parking reservation is confirmed.\n"
        f"Booking: {booking.booking_id}\n"
        f"Vehicle: {booking.vehicle_number} ({booking.vehicle_type.name})\n"
        f"Location: {booking.parking_lot.name}, {booking.parking_lot.address}\n"
        f"Allocated slot: {booking.slot.zone}-{booking.slot.number}, Floor {booking.slot.floor}\n"
        f"Reservation valid until: {_receipt_time(booking.reservation_expires_at)}\n\n"
        "Your PDF receipt is attached."
    )
    html_body = (
        f"<p>Hi {escape(booking.owner_name)},</p>"
        "<p>Your parking reservation is <strong>confirmed</strong>. Your PDF receipt is attached.</p>"
        "<table style=\"border-collapse:collapse;font-family:Arial,sans-serif\">"
        f"<tr><td style=\"padding:6px 16px 6px 0;color:#64748b\">Booking</td><td><strong>{escape(booking.booking_id)}</strong></td></tr>"
        f"<tr><td style=\"padding:6px 16px 6px 0;color:#64748b\">Vehicle</td><td>{escape(booking.vehicle_number)} ({escape(booking.vehicle_type.name)})</td></tr>"
        f"<tr><td style=\"padding:6px 16px 6px 0;color:#64748b\">Parking</td><td>{escape(booking.parking_lot.name)}</td></tr>"
        f"<tr><td style=\"padding:6px 16px 6px 0;color:#64748b\">Slot</td><td>{escape(booking.slot.zone)}-{booking.slot.number}, Floor {booking.slot.floor}</td></tr>"
        "</table>"
        "<p>Please arrive before the reservation expires and keep this receipt available at the entrance.</p>"
    )
    personalization = {
        "to": [{"email": owner_email}],
        "subject": subject,
    }
    if developer_email and developer_email != owner_email:
        personalization["bcc"] = [{"email": developer_email}]

    try:
        receipt = build_booking_receipt(booking)
        message = {
            "from": sender,
            "personalizations": [personalization],
            "content": [
                {"type": "text/plain", "value": text_body},
                {"type": "text/html", "value": html_body},
            ],
            "attachments": [
                {
                    "content": b64encode(receipt).decode("ascii"),
                    "filename": f"parking-receipt-{booking.booking_id}.pdf",
                    "type": "application/pdf",
                    "disposition": "attachment",
                }
            ],
        }
        response = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY).client.mail.send.post(request_body=message)
        if not 200 <= response.status_code < 300:
            logger.error(
                "SendGrid rejected receipt delivery for %s with status %s",
                booking.booking_id,
                response.status_code,
            )
            return _receipt_delivery(False, f"SendGrid returned HTTP {response.status_code}.")
        return _receipt_delivery(True)
    except HTTPError as error:
        detail = _sendgrid_error_detail(error)
        logger.error("SendGrid rejected receipt delivery for %s: %s", booking.booking_id, detail)
        return _receipt_delivery(False, f"SendGrid rejected the request: {detail}")
    except SystemExit as error:
        logger.error("SendGrid delivery unexpectedly stopped for %s: %s", booking.booking_id, error)
        return _receipt_delivery(False, "SendGrid delivery stopped unexpectedly.")
    except Exception as error:
        logger.exception("Unable to deliver SendGrid receipt for %s", booking.booking_id)
        return _receipt_delivery(False, f"SendGrid delivery failed: {error}")
