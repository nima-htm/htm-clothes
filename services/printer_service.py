"""
Print Service - PDF Generation using ReportLab with Full RTL/Persian Support
"""
import os
import tempfile
from datetime import datetime

from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, HRFlowable)
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import arabic_reshaper
from bidi.algorithm import get_display


class PrintService:
    # رنگ‌های هماهنگ با تم برنامه
    PRIMARY_COLOR = HexColor("#3b82f6")
    HEADER_BG = HexColor("#f8fafc")
    BORDER_COLOR = HexColor("#e2e8f0")
    TEXT_COLOR = HexColor("#1e293b")

    def __init__(self, font_path: str = None):
        """
        Args:
            font_path: مسیر فایل فونت Vazirmatn.ttf
                      اگر None باشد، از فونت پیش‌فرض Helvetica استفاده می‌شود
        """
        self.font_name = "Helvetica"
        self.font_bold = "Helvetica-Bold"

        if font_path and os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("Vazirmatn", font_path))
                self.font_name = "Vazirmatn"
                self.font_bold = "Vazirmatn"  # Vazirmatn-Regular به عنوان bold هم استفاده می‌شود
                print(f"✅ فونت '{font_path}' برای چاپ ثبت شد")
            except Exception as e:
                print(f"⚠️ خطا در ثبت فونت چاپ: {e}")

        self._styles = self._create_styles()

    @staticmethod
    def _fix_persian(text: str) -> str:
        """اصلاح نمایش متن فارسی در PDF"""
        if not text:
            return ""
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)

    def _create_styles(self) -> dict:
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='PersianTitle',
            fontName=self.font_bold,
            fontSize=16,
            alignment=TA_CENTER,
            textColor=self.TEXT_COLOR,
            spaceAfter=6 * mm,
        ))

        styles.add(ParagraphStyle(
            name='PersianNormal',
            fontName=self.font_name,
            fontSize=10,
            alignment=TA_RIGHT,
            textColor=self.TEXT_COLOR,
            leading=14,
        ))

        styles.add(ParagraphStyle(
            name='PersianSmall',
            fontName=self.font_name,
            fontSize=8,
            alignment=TA_RIGHT,
            textColor=HexColor("#64748b"),
            leading=10,
        ))

        styles.add(ParagraphStyle(
            name='PersianCenter',
            fontName=self.font_name,
            fontSize=10,
            alignment=TA_CENTER,
            textColor=self.TEXT_COLOR,
        ))

        return styles

    def generate_invoice_pdf(self, invoice, invoice_type: str = "sales",
                             output_path: str = None) -> str:
        """
        تولید PDF فاکتور فروش یا خرید

        Args:
            invoice: آبجکت SalesInvoice یا PurchaseInvoice
            invoice_type: "sales" یا "purchase"
            output_path: مسیر ذخیره. اگر None باشد، فایل موقت ساخته می‌شود

        Returns:
            مسیر فایل PDF تولید شده
        """
        if output_path is None:
            output_path = os.path.join(
                tempfile.gettempdir(),
                f"{invoice_type}_{invoice.invoice_number}.pdf"
            )

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A5,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

        elements = []
        is_sales = invoice_type == "sales"

        title_text = "فاکتور فروش" if is_sales else "فاکتور خرید"
        party_label = "مشتری" if is_sales else "فروشنده"

        if is_sales:
            party_name = invoice.customer.name
        else:
            party_name = invoice.supplier.name
        # ─── عنوان ───
        elements.append(Paragraph(self._fix_persian(title_text), self._styles['PersianTitle']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY_COLOR, spaceAfter=4 * mm))

        # ─── اطلاعات سربرگ ───
        header_data = [
            [self._fix_persian(f"شماره فاکتور: {invoice.invoice_number}"),
             self._fix_persian(f"تاریخ: {invoice.created_at.strftime('%Y/%m/%d')}")],
            [self._fix_persian(f"{party_label}: {party_name}"), ""],
        ]
        header_table = Table(header_data, colWidths=[doc.width / 2] * 2)
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3 * mm),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 4 * mm))

        # ─── جدول اقلام ───
        item_headers = ["#", "کد کالا", "نام کالا", "تعداد", "قیمت واحد", "جمع کل"]
        table_data = [[self._fix_persian(h) for h in item_headers]]

        for idx, item in enumerate(invoice.items, 1):
            product_code = item.product.code if hasattr(item, 'product') and item.product else "-"
            product_name = item.product.name if hasattr(item, 'product') and item.product else "-"

            row = [
                self._fix_persian(str(idx)),
                self._fix_persian(product_code),
                self._fix_persian(product_name),
                self._fix_persian(f"{item.quantity:,}"),
                self._fix_persian(f"{item.unit_price:,.0f}"),
                self._fix_persian(f"{item.total_price:,.0f}"),
            ]
            table_data.append(row)

        col_widths = [8 * mm, 22 * mm, 55 * mm, 18 * mm, 25 * mm, 25 * mm]
        items_table = Table(table_data, colWidths=col_widths, repeatRows=1)

        table_style_commands = [
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('BACKGROUND', (0, 0), (-1, 0), self.HEADER_BG),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('TOPPADDING', (0, 0), (-1, -1), 2 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2 * mm),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#fafafa")]),
        ]
        items_table.setStyle(TableStyle(table_style_commands))
        elements.append(items_table)
        elements.append(Spacer(1, 6 * mm))

        # ─── جمع و تخفیف ───
        totals_data = [
            [self._fix_persian(f"جمع کل: {invoice.total_price:,.0f} تومان")],
            [self._fix_persian(f"تخفیف: {invoice.discount:,.0f} تومان")],
            [self._fix_persian(f"قابل پرداخت: {invoice.final_total:,.0f} تومان")],
        ]
        totals_table = Table(totals_data, colWidths=[doc.width])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('TEXTCOLOR', (0, -1), (-1, -1), HexColor("#059669")),
            ('FONTNAME', (0, -1), (-1, -1), self.font_bold),
            ('TOPPADDING', (0, 0), (-1, -1), 2 * mm),
        ]))
        elements.append(totals_table)

        # ─── توضیحات ───
        if invoice.notes:
            elements.append(Spacer(1, 4 * mm))
            elements.append(Paragraph(
                self._fix_persian(f"توضیحات: {invoice.notes}"),
                self._styles['PersianSmall']
            ))

        # ─── پاورقی ───
        elements.append(Spacer(1, 10 * mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=self.BORDER_COLOR))
        elements.append(Spacer(1, 2 * mm))
        footer_text = f"تولید شده در {datetime.now().strftime('%Y/%m/%d %H:%M')} | Nima Clothes"
        elements.append(Paragraph(self._fix_persian(footer_text), self._styles['PersianSmall']))

        doc.build(elements)
        return output_path

    def generate_report_pdf(self, headers: list[str], rows: list[list[str]],
                            title: str, summary: str = "",
                            output_path: str = None) -> str:
        """تولید PDF برای گزارش‌ها"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(tempfile.gettempdir(), f"report_{timestamp}.pdf")

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                rightMargin=15 * mm, leftMargin=15 * mm,
                                topMargin=15 * mm, bottomMargin=15 * mm)

        elements = []
        elements.append(Paragraph(self._fix_persian(title), self._styles['PersianTitle']))
        elements.append(HRFlowable(width="100%", thickness=1, color=self.PRIMARY_COLOR, spaceAfter=4 * mm))

        table_data = [[self._fix_persian(h) for h in headers]]
        for row in rows:
            table_data.append([self._fix_persian(cell) for cell in row])

        n_cols = len(headers)
        col_width = doc.width / n_cols
        report_table = Table(table_data, colWidths=[col_width] * n_cols, repeatRows=1)
        report_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.TEXT_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.BORDER_COLOR),
            ('BACKGROUND', (0, 0), (-1, 0), self.HEADER_BG),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('TOPPADDING', (0, 0), (-1, -1), 2 * mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2 * mm),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#fafafa")]),
        ]))
        elements.append(report_table)

        if summary:
            elements.append(Spacer(1, 6 * mm))
            elements.append(Paragraph(self._fix_persian(summary), self._styles['PersianNormal']))

        doc.build(elements)
        return output_path

    @staticmethod
    def open_pdf(pdf_path: str):
        """باز کردن PDF با برنامه پیش‌فرض سیستم عامل"""
        import platform
        import subprocess

        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(pdf_path)
            elif system == "Darwin":
                subprocess.run(["open", pdf_path], check=False)
            else:
                subprocess.run(["xdg-open", pdf_path], check=False)
        except Exception as e:
            print(f"[WARN] Could not open PDF: {e}")