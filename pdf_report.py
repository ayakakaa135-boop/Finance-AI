"""
✨ PDF Report Generator for Finance AI
Generates professional monthly financial reports using ReportLab
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import date
import pandas as pd


# ── Color Palette ───────────────────────────────────────────────
INDIGO      = colors.HexColor("#6366f1")
INDIGO_DARK = colors.HexColor("#4f46e5")
GREEN       = colors.HexColor("#10b981")
RED         = colors.HexColor("#ef4444")
YELLOW      = colors.HexColor("#f59e0b")
BG_DARK     = colors.HexColor("#0f172a")
BG_CARD     = colors.HexColor("#1e293b")
TEXT_MAIN   = colors.HexColor("#e2e8f0")
TEXT_MUTED  = colors.HexColor("#94a3b8")
BORDER      = colors.HexColor("#334155")

CATEGORY_HEX = {
    "Food": "#f472b6", "Transport": "#60a5fa", "Shopping": "#fb923c",
    "Health": "#34d399", "Education": "#a78bfa", "Entertainment": "#fbbf24",
    "Housing": "#94a3b8", "Salary": "#10b981", "Other": "#6b7280",
}

CATEGORY_ICONS = {
    "Food": "🍔", "Transport": "🚗", "Shopping": "🛍️",
    "Health": "💊", "Education": "📚", "Entertainment": "🎮",
    "Housing": "🏠", "Salary": "💼", "Other": "📦",
}


def _styles():
    base = getSampleStyleSheet()
    custom = {}

    custom["title"] = ParagraphStyle(
        "title", parent=base["Normal"],
        fontSize=26, textColor=TEXT_MAIN, fontName="Helvetica-Bold",
        spaceAfter=4, alignment=TA_LEFT,
    )
    custom["subtitle"] = ParagraphStyle(
        "subtitle", parent=base["Normal"],
        fontSize=11, textColor=TEXT_MUTED, fontName="Helvetica",
        spaceAfter=2,
    )
    custom["section"] = ParagraphStyle(
        "section", parent=base["Normal"],
        fontSize=13, textColor=INDIGO, fontName="Helvetica-Bold",
        spaceBefore=16, spaceAfter=8,
    )
    custom["body"] = ParagraphStyle(
        "body", parent=base["Normal"],
        fontSize=9, textColor=TEXT_MAIN, fontName="Helvetica",
        leading=14,
    )
    custom["body_muted"] = ParagraphStyle(
        "body_muted", parent=base["Normal"],
        fontSize=8, textColor=TEXT_MUTED, fontName="Helvetica",
    )
    custom["kpi_value"] = ParagraphStyle(
        "kpi_value", parent=base["Normal"],
        fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER,
    )
    custom["kpi_label"] = ParagraphStyle(
        "kpi_label", parent=base["Normal"],
        fontSize=8, textColor=TEXT_MUTED, fontName="Helvetica",
        alignment=TA_CENTER,
    )
    custom["amount_green"] = ParagraphStyle(
        "amount_green", parent=base["Normal"],
        fontSize=9, textColor=GREEN, fontName="Helvetica-Bold",
        alignment=TA_RIGHT,
    )
    custom["amount_red"] = ParagraphStyle(
        "amount_red", parent=base["Normal"],
        fontSize=9, textColor=RED, fontName="Helvetica-Bold",
        alignment=TA_RIGHT,
    )
    return custom


def _kpi_table(total_in, total_out, net, styles):
    """3-column KPI summary table."""
    net_color = GREEN if net >= 0 else RED

    def kpi_cell(value_str, label, color):
        return [
            Paragraph(f'<font color="{color.hexval()}">{value_str}</font>', styles["kpi_value"]),
            Spacer(1, 2),
            Paragraph(label, styles["kpi_label"]),
        ]

    data = [[
        kpi_cell(f"{total_in:,.0f} SEK", "Total Income", GREEN),
        kpi_cell(f"{total_out:,.0f} SEK", "Total Expenses", RED),
        kpi_cell(f"{net:+,.0f} SEK", "Net Balance", net_color),
    ]]

    t = Table(data, colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BG_CARD]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    return t


def _category_breakdown_table(df_expenses, styles):
    """Category breakdown with mini progress bars (text-based)."""
    cat_sum = df_expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
    total = cat_sum.sum()

    header = [
        Paragraph("Category", styles["body_muted"]),
        Paragraph("Amount (SEK)", styles["body_muted"]),
        Paragraph("Share", styles["body_muted"]),
        Paragraph("Bar", styles["body_muted"]),
    ]
    rows = [header]

    for cat, amount in cat_sum.items():
        pct = amount / total * 100 if total > 0 else 0
        icon = CATEGORY_ICONS.get(cat, "📦")
        cat_color = colors.HexColor(CATEGORY_HEX.get(cat, "#6b7280"))
        bar_filled = int(pct / 5)  # Max 20 chars = 100%
        bar = "█" * bar_filled + "░" * (20 - bar_filled)

        rows.append([
            Paragraph(f'{icon} {cat}', styles["body"]),
            Paragraph(f'{amount:,.0f}', styles["amount_red"]),
            Paragraph(f'{pct:.1f}%', ParagraphStyle("pct", parent=styles["body"],
                      textColor=cat_color, fontName="Helvetica-Bold", alignment=TA_CENTER)),
            Paragraph(f'<font color="{cat_color.hexval()}">{bar[:bar_filled]}</font>'
                     f'<font color="#334155">{bar[bar_filled:]}</font>', styles["body"]),
        ])

    t = Table(rows, colWidths=[4.5 * cm, 3.5 * cm, 2.5 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INDIGO_DARK),
        ("BACKGROUND", (0, 1), (-1, -1), BG_CARD),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BG_CARD, colors.HexColor("#162032")]),
        ("TEXTCOLOR", (0, 0), (-1, 0), TEXT_MAIN),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
    ]))
    return t


def _transactions_table(df, styles, max_rows=20):
    """Recent transactions table."""
    df = df.sort_values("transaction_date", ascending=False).head(max_rows)

    header = [
        Paragraph("Date", styles["body_muted"]),
        Paragraph("Description", styles["body_muted"]),
        Paragraph("Category", styles["body_muted"]),
        Paragraph("Amount", styles["body_muted"]),
    ]
    rows = [header]

    for _, row in df.iterrows():
        is_income = row["transaction_type"] == "income"
        sign = "+" if is_income else "-"
        amount_style = styles["amount_green"] if is_income else styles["amount_red"]
        icon = CATEGORY_ICONS.get(row["category"], "📦")
        tx_date = str(row["transaction_date"])[:10]

        rows.append([
            Paragraph(tx_date, styles["body_muted"]),
            Paragraph(str(row["description"])[:45], styles["body"]),
            Paragraph(f'{icon} {row["category"]}', styles["body"]),
            Paragraph(f'{sign}{float(row["amount"]):,.0f}', amount_style),
        ])

    t = Table(rows, colWidths=[2.5 * cm, 7.5 * cm, 3.5 * cm, 3 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INDIGO_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BG_CARD, colors.HexColor("#162032")]),
        ("TEXTCOLOR", (0, 0), (-1, 0), TEXT_MAIN),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def generate_pdf_report(df: pd.DataFrame, month_label: str = None) -> bytes:
    """
    Generate a professional PDF financial report.
    Returns PDF bytes ready to download.
    """
    if month_label is None:
        month_label = date.today().strftime("%B %Y")

    styles = _styles()
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Finance AI Report — {month_label}",
    )

    story = []

    # ── Header ────────────────────────────────────────────────
    story.append(Paragraph("💎 Finance AI", styles["title"]))
    story.append(Paragraph(f"Financial Report · {month_label}", styles["subtitle"]))
    story.append(Paragraph(f"Generated on {date.today().strftime('%d %B %Y')}", styles["body_muted"]))
    story.append(HRFlowable(width="100%", thickness=1, color=INDIGO, spaceAfter=16))

    # ── KPI Summary ───────────────────────────────────────────
    df_copy = df.copy()
    df_copy["amount"] = pd.to_numeric(df_copy["amount"], errors="coerce").fillna(0)

    total_in  = df_copy[df_copy["transaction_type"] == "income"]["amount"].sum()
    total_out = df_copy[df_copy["transaction_type"] == "expense"]["amount"].sum()
    net       = total_in - total_out

    story.append(Paragraph("📊 Summary", styles["section"]))
    story.append(_kpi_table(total_in, total_out, net, styles))
    story.append(Spacer(1, 0.5 * cm))

    # ── Category Breakdown ────────────────────────────────────
    expenses = df_copy[df_copy["transaction_type"] == "expense"]
    if not expenses.empty:
        story.append(Paragraph("💰 Expenses by Category", styles["section"]))
        story.append(_category_breakdown_table(expenses, styles))
        story.append(Spacer(1, 0.5 * cm))

    # ── Monthly Summary ───────────────────────────────────────
    df_copy["transaction_date"] = pd.to_datetime(df_copy["transaction_date"], errors="coerce")
    df_copy["month"] = df_copy["transaction_date"].dt.to_period("M").astype(str)
    monthly = df_copy.groupby(["month", "transaction_type"])["amount"].sum().unstack(fill_value=0).reset_index()

    if not monthly.empty and "expense" in monthly.columns:
        story.append(Paragraph("📅 Monthly Breakdown", styles["section"]))

        m_header = [
            Paragraph("Month", styles["body_muted"]),
            Paragraph("Income (SEK)", styles["body_muted"]),
            Paragraph("Expenses (SEK)", styles["body_muted"]),
            Paragraph("Net (SEK)", styles["body_muted"]),
        ]
        m_rows = [m_header]
        for _, mrow in monthly.iterrows():
            inc = float(mrow.get("income", 0))
            exp = float(mrow.get("expense", 0))
            mn  = inc - exp
            net_color_hex = GREEN.hexval() if mn >= 0 else RED.hexval()
            m_rows.append([
                Paragraph(str(mrow["month"]), styles["body"]),
                Paragraph(f'{inc:,.0f}', styles["amount_green"]),
                Paragraph(f'{exp:,.0f}', styles["amount_red"]),
                Paragraph(
                    f'<font color="{net_color_hex}">{mn:+,.0f}</font>',
                    ParagraphStyle("net", parent=styles["body"], fontName="Helvetica-Bold", alignment=TA_RIGHT)
                ),
            ])

        mt = Table(m_rows, colWidths=[3.5 * cm, 4 * cm, 4.5 * cm, 4.5 * cm])
        mt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INDIGO_DARK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BG_CARD, colors.HexColor("#162032")]),
            ("TEXTCOLOR", (0, 0), (-1, 0), TEXT_MAIN),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(mt)
        story.append(Spacer(1, 0.5 * cm))

    # ── Recent Transactions ───────────────────────────────────
    story.append(Paragraph("🕐 Recent Transactions (last 20)", styles["section"]))
    story.append(_transactions_table(df_copy, styles))
    story.append(Spacer(1, 0.5 * cm))

    # ── Insights ──────────────────────────────────────────────
    if not expenses.empty:
        story.append(Paragraph("🧠 Key Insights", styles["section"]))
        top_cat = expenses.groupby("category")["amount"].sum().idxmax()
        top_pct = expenses.groupby("category")["amount"].sum().max() / expenses["amount"].sum() * 100
        avg_tx  = expenses["amount"].mean()
        tx_count = len(df_copy)

        insight_data = [
            [Paragraph(f"• Top spending category: {top_cat} ({top_pct:.0f}% of expenses)", styles["body"])],
            [Paragraph(f"• Average transaction: {avg_tx:,.0f} SEK", styles["body"])],
            [Paragraph(f"• Total transactions: {tx_count}", styles["body"])],
            [Paragraph(f"• Net position: {'Surplus ✅' if net >= 0 else 'Deficit ⚠️'} {abs(net):,.0f} SEK", styles["body"])],
        ]
        it = Table(insight_data, colWidths=[16.5 * cm])
        it.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_CARD),
            ("BOX", (0, 0), (-1, -1), 0.5, INDIGO),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(it)

    # ── Footer ────────────────────────────────────────────────
    story.append(Spacer(1, cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Generated by Finance AI · Powered by Google Gemini",
        ParagraphStyle("footer", parent=styles["body_muted"], alignment=TA_CENTER, fontSize=7)
    ))

    doc.build(story)
    return buffer.getvalue()
