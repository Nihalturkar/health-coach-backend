from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER
import io


def generate_report_pdf(report, user_name: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#2d6a4f"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2d6a4f"),
        spaceBefore=16,
        spaceAfter=8,
    )

    elements = []

    # Header
    elements.append(Paragraph("AI Health Coach", title_style))
    elements.append(Paragraph(
        f"Weekly Report — Week {report.week_number} | {user_name}",
        subtitle_style
    ))
    elements.append(Paragraph(
        f"{report.start_date} to {report.end_date}",
        subtitle_style
    ))

    # Stats table
    elements.append(Paragraph("Weekly Summary", heading_style))

    stats_data = [
        ["Metric", "Value"],
        ["Start Weight", f"{report.start_weight} kg" if report.start_weight else "—"],
        ["End Weight", f"{report.end_weight} kg" if report.end_weight else "—"],
        ["Avg Calories/day", str(report.avg_calories_consumed) if report.avg_calories_consumed else "—"],
        ["Avg Protein/day", f"{report.avg_protein_consumed}g" if report.avg_protein_consumed else "—"],
        ["Avg Water/day", f"{report.avg_water_ml} ml" if report.avg_water_ml else "—"],
        ["Avg Sleep", f"{report.avg_sleep_hours}h" if report.avg_sleep_hours else "—"],
        ["Workouts Completed", str(report.workouts_completed) if report.workouts_completed is not None else "—"],
        ["Workouts Skipped", str(report.workouts_skipped) if report.workouts_skipped is not None else "—"],
    ]

    table = Table(stats_data, colWidths=[8*cm, 8*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d6a4f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0fdf4")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1fae5")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(table)

    # AI Summary
    if report.ai_summary:
        elements.append(Paragraph("AI Analysis", heading_style))
        elements.append(Paragraph(report.ai_summary, styles["Normal"]))
        elements.append(Spacer(1, 12))

    # AI Suggestions
    if report.ai_suggestions:
        elements.append(Paragraph("Recommendations", heading_style))
        for suggestion in report.ai_suggestions:
            area = suggestion.get("area", "").title()
            text = suggestion.get("suggestion", "")
            elements.append(Paragraph(f"<b>{area}:</b> {text}", styles["Normal"]))
            elements.append(Spacer(1, 4))

    doc.build(elements)
    return buffer.getvalue()
