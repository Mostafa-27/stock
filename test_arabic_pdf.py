#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify Arabic PDF generation is working correctly
"""

import sys
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Try to import bidi for proper Arabic text processing
try:
    from bidi.algorithm import get_display
    BIDI_AVAILABLE = True
except ImportError:
    BIDI_AVAILABLE = False
    print("Warning: python-bidi not available. Arabic text may not display correctly.")

# Try to import arabic-reshaper for proper Arabic text shaping
try:
    import arabic_reshaper
    ARABIC_RESHAPER_AVAILABLE = True
except ImportError:
    ARABIC_RESHAPER_AVAILABLE = False
    print("Warning: arabic-reshaper not available. Arabic text may not display correctly.")

def register_arabic_font():
    """Register Arabic font for ReportLab PDF generation"""
    try:
        # Try to register fonts that support Arabic text
        font_paths = [
            "C:/Windows/Fonts/tahoma.ttf",  # Tahoma supports Arabic well
            "C:/Windows/Fonts/tahomabd.ttf",  # Tahoma Bold supports Arabic well
            "C:/Windows/Fonts/arial.ttf",  # Arial supports basic Arabic
            "C:/Windows/Fonts/arialbd.ttf",  # Arial Bold supports basic Arabic
            "C:/Windows/Fonts/calibri.ttf",  # Calibri supports Arabic
            "C:/Windows/Fonts/segoeui.ttf",  # Segoe UI supports Arabic
        ]
        
        # Try to find a valid font
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    # Register the main font
                    pdfmetrics.registerFont(TTFont('Arabic', font_path))
                    print(f"Successfully registered Arabic font: {font_path}")
                    
                    # Try to register bold variant
                    font_dir = os.path.dirname(font_path)
                    font_base = os.path.splitext(os.path.basename(font_path))[0]
                    bold_variants = [f"{font_base}bd.ttf", f"{font_base}b.ttf", f"{font_base}_bold.ttf"]
                    
                    for bold_variant in bold_variants:
                        bold_path = os.path.join(font_dir, bold_variant)
                        if os.path.exists(bold_path):
                            pdfmetrics.registerFont(TTFont('Arabic-Bold', bold_path))
                            print(f"Successfully registered Arabic Bold font: {bold_path}")
                            break
                    
                    return True
                except Exception as e:
                    print(f"Failed to register font {font_path}: {e}")
                    continue
        
        # If no system fonts work, try DejaVu Sans which often has good Unicode support
        dejavu_paths = [
            "C:/Windows/Fonts/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/DejaVuSans.ttf"
        ]
        
        for dejavu_path in dejavu_paths:
            if os.path.exists(dejavu_path):
                try:
                    pdfmetrics.registerFont(TTFont('Arabic', dejavu_path))
                    print(f"Successfully registered DejaVu Sans font: {dejavu_path}")
                    return True
                except Exception as e:
                    print(f"Failed to register DejaVu font {dejavu_path}: {e}")
        
        # Last resort: try Arial which is commonly available
        try:
            pdfmetrics.registerFont(TTFont('Arabic', 'C:/Windows/Fonts/arial.ttf'))
            print("Successfully registered Arial font as fallback")
            return True
        except Exception as e:
            print(f"Failed to register Arial font: {e}")
            return False
            
    except Exception as e:
        print(f"Font registration failed completely: {e}")
        return False

def get_font_name():
    """Get the appropriate font name for Arabic text"""
    font_registered = register_arabic_font()
    if font_registered:
        return 'Arabic'
    else:
        # Use built-in fonts that should support Unicode/Arabic better
        return 'Times-Roman'  # Times-Roman has better Unicode support than Helvetica

def format_arabic_text(text):
    """Format Arabic text for proper display in PDF"""
    if not text:
        return ""
    
    text_str = str(text)
    
    # First, reshape Arabic text to connect letters properly
    if ARABIC_RESHAPER_AVAILABLE:
        try:
            reshaped_text = arabic_reshaper.reshape(text_str)
        except Exception as e:
            print(f"Warning: Could not reshape Arabic text: {e}")
            reshaped_text = text_str
    else:
        reshaped_text = text_str
    
    # Then apply bidirectional algorithm for proper text direction
    if BIDI_AVAILABLE:
        try:
            # Use bidi algorithm to properly format Arabic text direction
            return get_display(reshaped_text)
        except Exception as e:
            print(f"Warning: Could not format Arabic text direction: {e}")
            return reshaped_text
    
    return reshaped_text

def test_arabic_pdf():
    """Test Arabic PDF generation"""
    try:
        # Create test PDF
        file_path = "test_arabic_report.pdf"
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Get appropriate font name
        font_name = get_font_name()
        print(f"Using font: {font_name}")
        
        # Create custom styles with Arabic font and RTL support
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center alignment
            fontName=font_name,
            wordWrap='RTL'  # Right-to-left text direction
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            fontName=font_name,
            alignment=2,  # Right alignment for Arabic text
            wordWrap='RTL'  # Right-to-left text direction
        )
        
        # Test Arabic title
        title = Paragraph(format_arabic_text("تقرير اختبار النص العربي"), title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Test Arabic text paragraph
        text_para = Paragraph(format_arabic_text("هذا نص تجريبي باللغة العربية لاختبار عرض النص في ملف PDF"), normal_style)
        story.append(text_para)
        story.append(Spacer(1, 12))
        
        # Test Arabic table
        data = [
            [format_arabic_text('رقم الفاتورة'), format_arabic_text('المورد'), format_arabic_text('المبلغ الإجمالي'), format_arabic_text('حالة الدفع')],
            ['001', format_arabic_text('مورد تجريبي'), '1000.00 ج.م', format_arabic_text('مدفوع')],
            ['002', format_arabic_text('مورد آخر'), '2500.50 ج.م', format_arabic_text('مدفوع جزئيا')],
            ['003', format_arabic_text('مورد ثالث'), '750.75 ج.م', format_arabic_text('متأخر')]
        ]
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),  # Right alignment for Arabic text
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical middle alignment
            ('FONTNAME', (0, 0), (-1, 0), font_name),  # Use dynamic font for headers
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), font_name),  # Use dynamic font for data
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 12))
        
        # Test summary
        summary_data = [
            [format_arabic_text('إجمالي الفواتير'), '3'],
            [format_arabic_text('إجمالي المبلغ'), '4251.25 ج.م'],
            [format_arabic_text('المبلغ المدفوع'), '3000.00 ج.م'],
            [format_arabic_text('المبلغ المتبقي'), '1251.25 ج.م']
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        
        # Build PDF
        doc.build(story)
        print(f"Test PDF created successfully: {file_path}")
        return True
        
    except Exception as e:
        print(f"Failed to create test PDF: {e}")
        return False

if __name__ == "__main__":
    print("Testing Arabic PDF generation...")
    success = test_arabic_pdf()
    if success:
        print("✅ Arabic PDF test completed successfully!")
    else:
        print("❌ Arabic PDF test failed!")
