from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib.colors import HexColor
from io import BytesIO
from datetime import date


# ── Brand colors ──────────────────────────────────────────
PRIMARY   = HexColor('#1a3c5e')   # dark navy — header bg
SECONDARY = HexColor('#2e86c1')   # medium blue — accents
ACCENT    = HexColor('#f0f4f8')   # light blue-gray — alt rows
SUCCESS   = HexColor('#1e8449')   # green — good grades
WARNING   = HexColor('#d4ac0d')   # amber — average grades
DANGER    = HexColor('#c0392b')   # red — poor grades
WHITE     = colors.white
LIGHT_GRAY = HexColor('#f2f3f4')
DARK_GRAY  = HexColor('#2c3e50')
MID_GRAY   = HexColor('#7f8c8d')


def get_grade(percentage):
    """Convert percentage to letter grade and remark."""
    if percentage >= 90:
        return 'A+', 'Outstanding'
    elif percentage >= 80:
        return 'A',  'Excellent'
    elif percentage >= 70:
        return 'B',  'Very Good'
    elif percentage >= 60:
        return 'C',  'Good'
    elif percentage >= 50:
        return 'D',  'Satisfactory'
    else:
        return 'F',  'Needs Improvement'


def get_grade_color(percentage):
    """Return color based on percentage."""
    if percentage >= 70:
        return SUCCESS
    elif percentage >= 50:
        return WARNING
    else:
        return DANGER


def generate_report_card(student, test, marks):
    """
    Generate a PDF report card for a student.

    Args:
        student: Student model instance
        test:    Test model instance
        marks:   QuerySet of Mark instances for this student and test

    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── 1. SCHOOL HEADER ──────────────────────────────────
    school_name_style = ParagraphStyle(
        'SchoolName',
        parent=styles['Normal'],
        fontSize=22,
        textColor=WHITE,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=2,
    )
    school_sub_style = ParagraphStyle(
        'SchoolSub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#d6eaf8'),
        alignment=TA_CENTER,
        fontName='Helvetica',
    )
    report_title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Normal'],
        fontSize=13,
        textColor=HexColor('#aed6f1'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceBefore=6,
    )

    header_data = [[
        Paragraph('NEDIANS ACADEMY', school_name_style),
    ], [
        Paragraph(
            'Excellence in Education · Knowledge · Character · Service',
            school_sub_style
        ),
    ], [
        Paragraph('STUDENT REPORT CARD', report_title_style),
    ]]

    header_table = Table(header_data, colWidths=[180 * mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY),
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, 0),  14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', [6, 6, 0, 0]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))

    # ── 2. STUDENT INFO CARD ──────────────────────────────
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=8,
        textColor=MID_GRAY,
        fontName='Helvetica',
    )
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=11,
        textColor=DARK_GRAY,
        fontName='Helvetica-Bold',
    )

    total_obtained = sum(m.obtained_marks for m in marks)
    total_marks    = sum(m.total_marks    for m in marks)
    overall_pct    = round(
        (total_obtained / total_marks * 100), 2
    ) if total_marks > 0 else 0
    grade, remark  = get_grade(overall_pct)

    info_data = [
        [
            Paragraph('STUDENT NAME', label_style),
            Paragraph('STUDENT ID', label_style),
            Paragraph('CLASS', label_style),
            Paragraph('OVERALL GRADE', label_style),
        ],
        [
            Paragraph(student.full_name, value_style),
            Paragraph(student.student_id, value_style),
            Paragraph(str(student.student_class), value_style),
            Paragraph(grade, ParagraphStyle(
                'Grade',
                parent=styles['Normal'],
                fontSize=18,
                textColor=get_grade_color(overall_pct),
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
            )),
        ],
        [
            Paragraph('EXAM / TEST', label_style),
            Paragraph('EXAM DATE', label_style),
            Paragraph('TOTAL MARKS', label_style),
            Paragraph('PERCENTAGE', label_style),
        ],
        [
            Paragraph(test.name, value_style),
            Paragraph(str(test.date), value_style),
            Paragraph(f'{total_obtained} / {total_marks}', value_style),
            Paragraph(f'{overall_pct}%', ParagraphStyle(
                'Pct',
                parent=styles['Normal'],
                fontSize=13,
                textColor=get_grade_color(overall_pct),
                fontName='Helvetica-Bold',
            )),
        ],
    ]

    info_table = Table(
        info_data,
        colWidths=[50 * mm, 40 * mm, 50 * mm, 40 * mm]
    )
    info_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOX',           (0, 0), (-1, -1), 0.5, HexColor('#d5d8dc')),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, HexColor('#e5e8e8')),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('BACKGROUND',    (3, 1), (3, 1),   HexColor('#eafaf1')),
        ('BACKGROUND',    (3, 3), (3, 3),   HexColor('#eafaf1')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 5 * mm))

    # ── 3. MARKS TABLE ────────────────────────────────────
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Normal'],
        fontSize=11,
        textColor=WHITE,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
    )

    section_header = Table(
        [[Paragraph('  SUBJECT-WISE PERFORMANCE', section_style)]],
        colWidths=[180 * mm]
    )
    section_header.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), SECONDARY),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(section_header)

    # Table header row
    th_style = ParagraphStyle(
        'TH',
        parent=styles['Normal'],
        fontSize=9,
        textColor=WHITE,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
    )
    marks_header = [
        Paragraph('NO.',        th_style),
        Paragraph('SUBJECT',    th_style),
        Paragraph('OBTAINED',   th_style),
        Paragraph('TOTAL',      th_style),
        Paragraph('PERCENTAGE', th_style),
        Paragraph('GRADE',      th_style),
        Paragraph('REMARKS',    th_style),
    ]

    marks_rows = [marks_header]

    td_center = ParagraphStyle(
        'TDCenter',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_GRAY,
        fontName='Helvetica',
        alignment=TA_CENTER,
    )
    td_left = ParagraphStyle(
        'TDLeft',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_GRAY,
        fontName='Helvetica',
        alignment=TA_LEFT,
    )

    for i, mark in enumerate(marks, start=1):
        pct        = mark.percentage
        g, rem     = get_grade(pct)
        row_bg     = ACCENT if i % 2 == 0 else WHITE
        grade_color = get_grade_color(pct)

        marks_rows.append([
            Paragraph(str(i),               td_center),
            Paragraph(mark.subject.name,    td_left),
            Paragraph(str(mark.obtained_marks), td_center),
            Paragraph(str(mark.total_marks),    td_center),
            Paragraph(f'{pct}%',            td_center),
            Paragraph(g,  ParagraphStyle(
                'GradeCell',
                parent=styles['Normal'],
                fontSize=10,
                textColor=grade_color,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
            )),
            Paragraph(rem, td_center),
        ])

    marks_table = Table(
        marks_rows,
        colWidths=[12*mm, 55*mm, 25*mm, 22*mm, 28*mm, 18*mm, 35*mm]
    )

    table_style = [
        # Header row
        ('BACKGROUND',    (0, 0), (-1, 0),  PRIMARY),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  WHITE),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  9),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('GRID',          (0, 0), (-1, -1), 0.3, HexColor('#d5d8dc')),
        ('BOX',           (0, 0), (-1, -1), 0.8, HexColor('#aab7b8')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, ACCENT]),
    ]
    marks_table.setStyle(TableStyle(table_style))
    elements.append(marks_table)
    elements.append(Spacer(1, 5 * mm))

    # ── 4. RESULT SUMMARY BOX ─────────────────────────────
    summary_label = ParagraphStyle(
        'SumLabel',
        parent=styles['Normal'],
        fontSize=9,
        textColor=MID_GRAY,
        fontName='Helvetica',
        alignment=TA_CENTER,
    )
    summary_value = ParagraphStyle(
        'SumValue',
        parent=styles['Normal'],
        fontSize=13,
        textColor=DARK_GRAY,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
    )

    summary_data = [
        [
            Paragraph('TOTAL OBTAINED', summary_label),
            Paragraph('TOTAL MARKS',    summary_label),
            Paragraph('PERCENTAGE',     summary_label),
            Paragraph('GRADE',          summary_label),
            Paragraph('REMARKS',        summary_label),
        ],
        [
            Paragraph(str(total_obtained), summary_value),
            Paragraph(str(total_marks),    summary_value),
            Paragraph(f'{overall_pct}%',   ParagraphStyle(
                'SumPct',
                parent=styles['Normal'],
                fontSize=13,
                textColor=get_grade_color(overall_pct),
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
            )),
            Paragraph(grade, ParagraphStyle(
                'SumGrade',
                parent=styles['Normal'],
                fontSize=16,
                textColor=get_grade_color(overall_pct),
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
            )),
            Paragraph(remark, ParagraphStyle(
                'SumRemark',
                parent=styles['Normal'],
                fontSize=11,
                textColor=get_grade_color(overall_pct),
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
            )),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[36*mm, 36*mm, 36*mm, 36*mm, 36*mm]
    )
    summary_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  HexColor('#d6eaf8')),
        ('BACKGROUND',    (0, 1), (-1, 1),  HexColor('#eaf4fb')),
        ('BOX',           (0, 0), (-1, -1), 0.8, SECONDARY),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, HexColor('#aed6f1')),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 6 * mm))

    # ── 5. FOOTER ─────────────────────────────────────────
    elements.append(HRFlowable(
        width='100%',
        thickness=0.5,
        color=HexColor('#aab7b8')
    ))
    elements.append(Spacer(1, 3 * mm))

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=MID_GRAY,
        alignment=TA_CENTER,
        fontName='Helvetica',
    )
    generated_on = date.today().strftime('%B %d, %Y')
    elements.append(Paragraph(
        f'This report card was generated on {generated_on} · '
        f'Nedians Academy · Confidential',
        footer_style
    ))
    elements.append(Spacer(1, 4 * mm))

    # Signature row
    sig_data = [[
        Paragraph('_________________\nClass Teacher', ParagraphStyle(
            'Sig',
            parent=styles['Normal'],
            fontSize=9,
            textColor=DARK_GRAY,
            fontName='Helvetica',
            alignment=TA_CENTER,
        )),
        Paragraph('_________________\nPrincipal', ParagraphStyle(
            'Sig',
            parent=styles['Normal'],
            fontSize=9,
            textColor=DARK_GRAY,
            fontName='Helvetica',
            alignment=TA_CENTER,
        )),
        Paragraph('_________________\nParent / Guardian', ParagraphStyle(
            'Sig',
            parent=styles['Normal'],
            fontSize=9,
            textColor=DARK_GRAY,
            fontName='Helvetica',
            alignment=TA_CENTER,
        )),
    ]]
    sig_table = Table(sig_data, colWidths=[60*mm, 60*mm, 60*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN',  (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(sig_table)

    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer