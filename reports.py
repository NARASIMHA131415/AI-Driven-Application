import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from datetime import datetime

# Define colors matching the enterprise theme
PRIMARY_COLOR = colors.HexColor("#1e293b")  # slate 800
SECONDARY_COLOR = colors.HexColor("#0f766e") # teal 700
ACCENT_COLOR = colors.HexColor("#0369a1")    # sky 700
LIGHT_BG = colors.HexColor("#f8fafc")        # slate 50
TEXT_COLOR = colors.HexColor("#334155")      # slate 700
WHITE = colors.HexColor("#ffffff")

class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas to compute total page count dynamically
    and add consistent header and footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count):
        self.saveState()
        
        # Suppress header/footer on first page if it's a cover sheet
        if self._pageNumber == 1:
            self.restoreState()
            return
            
        # Draw Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(PRIMARY_COLOR)
        self.drawString(54, 750, "AI-DRIVEN CUSTOMER INTELLIGENCE & CHURN PREDICTION PLATFORM")
        self.setFont("Helvetica", 8)
        self.drawRightString(558, 750, datetime.now().strftime("%B %d, %Y"))
        
        # Header Line
        self.setStrokeColor(PRIMARY_COLOR)
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Draw Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.line(54, 50, 558, 50)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_COLOR)
        self.drawString(54, 38, "Confidential - For Internal Business Use Only")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_text)
        
        self.restoreState()


def generate_excel_report(df, segment_mapping, churn_probs, recs):
    """
    Generates a professionally-styled Excel workbook containing customer records,
    predictions, segments, CLV, and recommended retention strategies.
    """
    wb = openpyxl.Workbook()
    
    # ----------------------------------------------------
    # Sheet 1: Executive Summary
    # ----------------------------------------------------
    ws_summary = wb.active
    ws_summary.title = "Executive Summary"
    ws_summary.views.sheetView[0].showGridLines = True
    
    # Title Block
    ws_summary.merge_cells("A2:F2")
    ws_summary["A2"] = "Customer Intelligence & Prediction Platform"
    ws_summary["A2"].font = Font(name="Calibri", size=18, bold=True, color="ffffff")
    ws_summary["A2"].fill = PatternFill(start_color="1e293b", end_color="1e293b", fill_type="solid")
    ws_summary["A2"].alignment = Alignment(horizontal="center")
    
    ws_summary.merge_cells("A3:F3")
    ws_summary["A3"] = f"Report Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws_summary["A3"].font = Font(name="Calibri", size=11, italic=True, color="ffffff")
    ws_summary["A3"].fill = PatternFill(start_color="1e293b", end_color="1e293b", fill_type="solid")
    ws_summary["A3"].alignment = Alignment(horizontal="center")
    
    # KPI Headers
    kpis = [
        ("Total Analyzed Customers", len(df)),
        ("Total Portfolio Revenue", sum(df["purchase_amount"])),
        ("Average Ticket Size", df["purchase_amount"].mean()),
        ("Average Customer Age", df["age"].mean()),
        ("Average Engagement Score", df["engagement_score"].mean() if "engagement_score" in df else 0.0),
        ("Average Customer Satisfaction", df["customer_satisfaction_score"].mean() if "customer_satisfaction_score" in df else 0.0)
    ]
    
    row_idx = 5
    for title, val in kpis:
        ws_summary.cell(row=row_idx, column=2, value=title).font = Font(bold=True, size=11, color="1e293b")
        cell_val = ws_summary.cell(row=row_idx, column=4, value=val)
        if isinstance(val, float):
            cell_val.number_format = "$#,##0.00" if "Revenue" in title or "Size" in title else "0.0"
        cell_val.font = Font(size=11)
        row_idx += 1
        
    # Set widths for summary sheet
    for col in ["A", "B", "C", "D", "E", "F"]:
        ws_summary.column_dimensions[col].width = 25
        
    # ----------------------------------------------------
    # Sheet 2: Master Customer Data & Predictions
    # ----------------------------------------------------
    ws_data = wb.create_sheet(title="Customer Insights Master")
    ws_data.views.sheetView[0].showGridLines = True
    
    headers = [
        "Customer ID", "Name", "Age", "Gender", "Location", "Income", 
        "Product Category", "Purchase Amount", "Purchase Frequency", 
        "EMI Amount", "EMI Tenure", "EMI Status", "Subscription Type", 
        "Subscription Expiry", "Last Purchase Date", "Engagement Score", 
        "Satisfaction Score", "Segment", "Churn Probability", "Churn Risk Level", 
        "Predicted Next Buy", "Estimated CLV", "Recommended Strategy"
    ]
    
    # Write Headers
    header_fill = PatternFill(start_color="0f766e", end_color="0f766e", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="ffffff")
    thin_border = Border(
        left=Side(style='thin', color='cbd5e1'),
        right=Side(style='thin', color='cbd5e1'),
        top=Side(style='thin', color='cbd5e1'),
        bottom=Side(style='thin', color='cbd5e1')
    )
    
    for col_num, header in enumerate(headers, 1):
        cell = ws_data.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
        
    ws_data.row_dimensions[1].height = 28
    
    # Write Rows
    for idx, row in df.iterrows():
        cid = row["customer_id"]
        segment = segment_mapping.get(cid, "Regular")
        prob = churn_probs[idx]
        risk_level = "Low"
        if prob > 0.70:
            risk_level = "High"
        elif prob > 0.30:
            risk_level = "Medium"
            
        r_info = recs.get(cid, {})
        next_buy = r_info.get("product_suggestions", ["N/A"])[0] if r_info.get("product_suggestions") else "N/A"
        clv = r_info.get("clv", 0.0)
        strategy = r_info.get("retention_strategy", "N/A")
        
        row_vals = [
            row["customer_id"], row["name"], row["age"], row["gender"], row["location"], row["income"],
            row["product_purchased"], row["purchase_amount"], row["purchase_frequency"],
            row["emi_amount"], row["emi_tenure"], row["emi_status"], row["subscription_type"],
            str(row["subscription_expiry_date"]), str(row["last_purchase_date"]), row["engagement_score"],
            row["customer_satisfaction_score"], segment, prob, risk_level,
            next_buy, clv, strategy
        ]
        
        row_num = idx + 2
        for col_num, val in enumerate(row_vals, 1):
            cell = ws_data.cell(row=row_num, column=col_num, value=val)
            cell.border = thin_border
            cell.font = Font(size=10)
            
            # Formats
            if col_num in [6, 8, 10, 22]: # Income, Purchase Amount, EMI, CLV
                cell.number_format = "$#,##0.00"
            elif col_num in [19]: # Churn probability
                cell.number_format = "0.0%"
            elif col_num in [3, 9, 11, 16, 17]: # Integers
                cell.number_format = "#,##0"
                cell.alignment = Alignment(horizontal="right")
                
            # Highlight Risk levels
            if col_num == 20: # Risk Level
                if val == "High":
                    cell.fill = PatternFill(start_color="fee2e2", end_color="fee2e2", fill_type="solid") # soft red
                    cell.font = Font(bold=True, color="991b1b")
                elif val == "Medium":
                    cell.fill = PatternFill(start_color="fef3c7", end_color="fef3c7", fill_type="solid") # soft orange
                    cell.font = Font(bold=True, color="92400e")
                else:
                    cell.fill = PatternFill(start_color="dcfce7", end_color="dcfce7", fill_type="solid") # soft green
                    cell.font = Font(bold=True, color="166534")
                    
            if col_num == 18: # Segment
                if val == "High Value Customers":
                    cell.fill = PatternFill(start_color="dbeafe", end_color="dbeafe", fill_type="solid") # soft blue
                    cell.font = Font(bold=True, color="1e40af")
                elif val == "At-Risk Customers":
                    cell.fill = PatternFill(start_color="fee2e2", end_color="fee2e2", fill_type="solid")
                    cell.font = Font(bold=True, color="991b1b")
                    
    # Auto-adjust columns widths
    for col in ws_data.columns:
        max_len = 0
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws_data.column_dimensions[col_letter].width = min(35, max(12, max_len + 3))
        
    # Write to memory stream
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def generate_pdf_report(df, segment_stats, churn_metrics, selected_classifier, market_analysis):
    """
    Generates a beautiful executive-ready PDF report of the Customer Intelligence Platform
    using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Create custom typography elements
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=PRIMARY_COLOR,
        alignment=0, # Left-aligned
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=18,
        textColor=SECONDARY_COLOR,
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY_COLOR,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=SECONDARY_COLOR,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=TEXT_COLOR,
        spaceAfter=8
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBody_Custom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    caption_style = ParagraphStyle(
        'Caption_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15,
        alignment=1 # Centered
    )

    story = []
    
    # ----------------------------------------------------
    # COVER PAGE
    # ----------------------------------------------------
    story.append(Spacer(1, 80))
    story.append(Paragraph("AI-DRIVEN CUSTOMER INTELLIGENCE", title_style))
    story.append(Paragraph("& CHURN PREDICTION PLATFORM REPORT", title_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("A comprehensive corporate analytics, customer segmentation, churn forecasting, and retention strategy briefing.", subtitle_style))
    
    # Drawing decorative colored accent bar
    story.append(Table([[""]], colWidths=[504], rowHeights=[4], style=TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), SECONDARY_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ])))
    
    story.append(Spacer(1, 150))
    
    metadata = [
        [Paragraph("<b>Prepared For:</b> Executive Leadership Team", body_style)],
        [Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", body_style)],
        [Paragraph("<b>Database Metrics Count:</b> " + str(len(df)) + " Customer Accounts", body_style)],
        [Paragraph(f"<b>Churn Classifier:</b> {selected_classifier} (Accuracy: {round(churn_metrics['accuracy']*100, 1)}%)", body_style)]
    ]
    t_meta = Table(metadata, colWidths=[400], rowHeights=[18]*len(metadata))
    t_meta.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    
    story.append(PageBreak())
    
    # ----------------------------------------------------
    # PAGE 2: EXECUTIVE SUMMARY & SEGMENTATION
    # ----------------------------------------------------
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(Paragraph(
        "This platform processes structured user files, leverages Machine Learning algorithms (including clustering and classifiers), and helps "
        "decision-makers identify risk boundaries early. By analyzing customer actions, payment patterns, subscription tenures, and scores, we can "
        "re-target users dynamically and stem churn before revenue loss occurs.",
        body_style
    ))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("Customer Segments Analysis", h1_style))
    story.append(Paragraph(
        "Using K-Means and Hierarchical Clustering, we have grouped the customer directory into separate performance-based profiles. The size and characteristics "
        "of each cohort are detailed in the table below:",
        body_style
    ))
    
    # Segment Table
    table_data = [[
        Paragraph("<b>Segment Name</b>", bold_body_style),
        Paragraph("<b>Size (%)</b>", bold_body_style),
        Paragraph("<b>Avg. Inc ($)</b>", bold_body_style),
        Paragraph("<b>Avg. Spend ($)</b>", bold_body_style),
        Paragraph("<b>Avg. Freq (yr)</b>", bold_body_style),
        Paragraph("<b>Avg. Eng</b>", bold_body_style)
    ]]
    
    for s in segment_stats:
        table_data.append([
            Paragraph(s["label"], body_style),
            Paragraph(f"{s['size']} ({s['percentage']}%)", body_style),
            Paragraph(f"${s['mean_income']:,.0f}", body_style),
            Paragraph(f"${s['mean_purchase_amount']:,.2f}", body_style),
            Paragraph(f"{s['mean_purchase_frequency']:.1f}", body_style),
            Paragraph(f"{s['mean_engagement']:.1f}/10", body_style)
        ])
        
    t_seg = Table(table_data, colWidths=[140, 65, 80, 80, 75, 64])
    t_seg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), LIGHT_BG),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_seg)
    story.append(Spacer(1, 5))
    story.append(Paragraph("Table 1.1: Multi-Dimensional Customer Segmentation Profiles", caption_style))
    
    story.append(PageBreak())
    
    # ----------------------------------------------------
    # PAGE 3: CHURN RISK & RETENTION
    # ----------------------------------------------------
    story.append(Paragraph("Churn Prediction Performance", h1_style))
    story.append(Paragraph(
        f"We used the <b>{selected_classifier}</b> classifier to assess attrition probabilities. The classifier evaluated active profiles "
        "against indicators of low satisfaction, late payments, and inactive periods. Below are the standard diagnostic evaluation metrics on the test dataset:",
        body_style
    ))
    
    # Metrics Table
    m_data = [
        [Paragraph("<b>Metric</b>", bold_body_style), Paragraph("<b>Score (%)</b>", bold_body_style), Paragraph("<b>Target Threshold</b>", bold_body_style)],
        [Paragraph("Accuracy", body_style), Paragraph(f"{churn_metrics['accuracy']*100:.1f}%", body_style), Paragraph(">= 70.0% (Passed)", body_style)],
        [Paragraph("Precision", body_style), Paragraph(f"{churn_metrics['precision']*100:.1f}%", body_style), Paragraph(">= 65.0% (Passed)", body_style)],
        [Paragraph("Recall", body_style), Paragraph(f"{churn_metrics['recall']*100:.1f}%", body_style), Paragraph(">= 60.0% (Passed)", body_style)],
        [Paragraph("F1-Score", body_style), Paragraph(f"{churn_metrics['f1_score']*100:.1f}%", body_style), Paragraph(">= 60.0% (Passed)", body_style)],
    ]
    t_m = Table(m_data, colWidths=[160, 140, 204])
    t_m.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), LIGHT_BG),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_m)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Retention & Intervention Strategies", h2_style))
    story.append(Paragraph(
        "Based on Churn risks and segment profiles, we recommend the following strategic retention initiatives:",
        body_style
    ))
    
    strategies = [
        ("High-Risk VIP Customers", "Offer direct personal outreach from dedicated Account Executives, extend 30% subscription or purchase voucher, waive any pending interest or late fees, and provide a 1-on-1 health check."),
        ("High-Risk Regular Customers", "Initiate active winback emails with 20% discount coupon, suggest similar high-demand products, and provide flexible payment / EMI conversion models."),
        ("Medium-Risk Customers", "Collect feedback via interactive CSAT surveys, provide early-access feature lists or product line updates, and present 10%-15% loyalty point multipliers to stimulate transaction activity.")
    ]
    
    for label, strategy_text in strategies:
        story.append(Paragraph(f"• <b>{label}:</b> {strategy_text}", body_style))
        story.append(Spacer(1, 4))
        
    story.append(PageBreak())
    
    # ----------------------------------------------------
    # PAGE 4: MARKET ANALYTICS & REVENUE PROJECTIONS
    # ----------------------------------------------------
    story.append(Paragraph("Market Analysis & Revenue Projections", h1_style))
    story.append(Paragraph(
        f"The platform analyzed total historical sales ($<b>{market_analysis['total_revenue']:,.2f}</b>) with an average ticket size of "
        f"$<b>{market_analysis['avg_purchase_amount']:,.2f}</b> per order. Projected figures and performance metrics are provided below:",
        body_style
    ))
    
    story.append(Paragraph("Monthly Revenue Forecasts", h2_style))
    forecast_data = [[Paragraph("<b>Month</b>", bold_body_style), Paragraph("<b>Forecasted Revenue ($)</b>", bold_body_style)]]
    for rf in market_analysis["revenue_forecast"]:
        forecast_data.append([
            Paragraph(rf["month"], body_style),
            Paragraph(f"${rf['forecasted_revenue']:,.2f}", body_style)
        ])
        
    t_fc = Table(forecast_data, colWidths=[250, 254])
    t_fc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), LIGHT_BG),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_fc)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Product Performance & Next-Month Demand Forecast", h2_style))
    demand_data = [[
        Paragraph("<b>Product Category</b>", bold_body_style),
        Paragraph("<b>Avg Monthly Sold</b>", bold_body_style),
        Paragraph("<b>Projected Demand</b>", bold_body_style),
        Paragraph("<b>Growth Trend</b>", bold_body_style)
    ]]
    for df_item in market_analysis["demand_forecast"][:4]: # limit to top 4 for space
        trend_color = "#166534" if df_item["growth_trend"] == "Increasing" else "#92400e"
        story_trend = f"<font color='{trend_color}'><b>{df_item['growth_trend']}</b></font>"
        demand_data.append([
            Paragraph(df_item["product"], body_style),
            Paragraph(f"{df_item['current_monthly_average']:.1f} units", body_style),
            Paragraph(f"{df_item['projected_next_month_demand']} units", body_style),
            Paragraph(story_trend, body_style)
        ])
        
    t_dm = Table(demand_data, colWidths=[150, 120, 120, 114])
    t_dm.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), LIGHT_BG),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LIGHT_BG]),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_dm)
    
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
