import io
from datetime import datetime
from typing import Any, Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_report(
    title: str,
    teacher_name: str,
    target_name: str,
    report_type: str,
    stats: Dict[str, Any],
    items: List[Dict[str, Any]],
) -> io.BytesIO:
    """Generate a clean, professional PDF report using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1E293B"),
        fontName="Helvetica-Bold",
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        fontName="Helvetica",
    )
    header_cell_style = ParagraphStyle(
        "HeaderCell",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        alignment=1,
    )
    body_cell_style = ParagraphStyle(
        "BodyCell",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
        fontName="Helvetica",
    )
    bold_cell_style = ParagraphStyle(
        "BoldBodyCell",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
        fontName="Helvetica-Bold",
    )

    # 1. Header Section
    story.append(Paragraph(f"<b>TRACKER APP</b> — Professional Task Management", subtitle_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(title, title_style))
    story.append(
        Paragraph(
            f"<b>O'qituvchi:</b> {teacher_name} &nbsp;|&nbsp; <b>Hisobot turi:</b> {report_type} ({target_name}) &nbsp;|&nbsp; <b>Sana:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=14))

    # 2. Key Metrics Summary Cards in Table
    stat_data = [
        [
            Paragraph("<b>Jami talabalar</b>", subtitle_style),
            Paragraph("<b>Bajarilgan ishlar</b>", subtitle_style),
            Paragraph("<b>O'rtacha ball</b>", subtitle_style),
            Paragraph("<b>O'zlashtirish</b>", subtitle_style),
        ],
        [
            Paragraph(f"<font size=13 color='#4F46E5'><b>{stats.get('total_students', 0)} ta</b></font>", body_cell_style),
            Paragraph(f"<font size=13 color='#10B981'><b>{stats.get('completed_tasks', 0)} ta</b></font>", body_cell_style),
            Paragraph(f"<font size=13 color='#3B82F6'><b>{stats.get('avg_score', 0)} / 100</b></font>", body_cell_style),
            Paragraph(f"<font size=13 color='#8B5CF6'><b>{stats.get('completion_rate', 0)}%</b></font>", body_cell_style),
        ],
    ]
    summary_table = Table(stat_data, colWidths=[130, 130, 130, 130])
    summary_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # 3. Main Data Table
    story.append(Paragraph("<b>Batafsil ma'lumotlar jadvali:</b>", ParagraphStyle("SectionTitle", parent=styles["Heading2"], fontSize=12, leading=16, textColor=colors.HexColor("#334155"), spaceAfter=8)))

    table_data = [[
        Paragraph("<b>№</b>", header_cell_style),
        Paragraph("<b>Talaba / Vazifa</b>", header_cell_style),
        Paragraph("<b>Guruh</b>", header_cell_style),
        Paragraph("<b>Holati</b>", header_cell_style),
        Paragraph("<b>Muddat</b>", header_cell_style),
        Paragraph("<b>Baho</b>", header_cell_style),
    ]]

    for idx, item in enumerate(items, 1):
        status_color = "#10B981" if item.get("status") in ["GRADED", "SUBMITTED"] else ("#EF4444" if item.get("status") == "LATE" else "#F59E0B")
        table_data.append([
            Paragraph(str(idx), body_cell_style),
            Paragraph(f"<b>{item.get('title', '-')}</b>", bold_cell_style),
            Paragraph(str(item.get("group", "-")), body_cell_style),
            Paragraph(f"<font color='{status_color}'><b>{item.get('status', '-')}</b></font>", body_cell_style),
            Paragraph(str(item.get("deadline", "-")), body_cell_style),
            Paragraph(f"<b>{item.get('score', '-')}</b>", bold_cell_style),
        ])

    main_table = Table(table_data, colWidths=[25, 175, 100, 85, 80, 55])
    main_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(main_table)

    # 4. Footer
    story.append(Spacer(1, 20))
    story.append(Paragraph("Hujjat Tracker App platformasi orqali avtomatik shakllantirilgan va rasmiy hisobot kuchiga ega.", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
