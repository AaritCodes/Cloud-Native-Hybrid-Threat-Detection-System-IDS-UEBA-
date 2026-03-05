"""
Convert all markdown files to PDF
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re
import os
import glob

def convert_md_to_pdf(md_file, pdf_file):
    """Convert a markdown file to PDF"""
    try:
        # Read markdown file
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create PDF
        pdf = SimpleDocTemplate(pdf_file, pagesize=letter,
                               rightMargin=0.75*inch, leftMargin=0.75*inch,
                               topMargin=0.75*inch, bottomMargin=0.75*inch)
        
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='darkblue',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=styles['Heading1'],
            fontSize=16,
            textColor='darkblue',
            spaceAfter=12,
            spaceBefore=12
        )
        
        heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='navy',
            spaceAfter=10,
            spaceBefore=10
        )
        
        heading3_style = ParagraphStyle(
            'CustomHeading3',
            parent=styles['Heading3'],
            fontSize=12,
            textColor='navy',
            spaceAfter=8,
            spaceBefore=8
        )
        
        code_style = ParagraphStyle(
            'Code',
            parent=styles['Code'],
            fontSize=8,
            leftIndent=20,
            rightIndent=20,
            spaceAfter=10,
            spaceBefore=10
        )
        
        # Parse markdown
        lines = content.split('\n')
        in_code_block = False
        code_buffer = []
        
        for line in lines:
            # Code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    # End code block
                    code_text = '\n'.join(code_buffer)
                    if code_text.strip():
                        story.append(Preformatted(code_text, code_style))
                    code_buffer = []
                    in_code_block = False
                else:
                    # Start code block
                    in_code_block = True
                continue
            
            if in_code_block:
                code_buffer.append(line)
                continue
            
            # Headers
            if line.startswith('# '):
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph(line[2:], title_style))
            elif line.startswith('## '):
                story.append(Spacer(1, 0.15*inch))
                story.append(Paragraph(line[3:], heading1_style))
            elif line.startswith('### '):
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(line[4:], heading2_style))
            elif line.startswith('#### '):
                story.append(Paragraph(line[5:], heading3_style))
            
            # Horizontal rules
            elif line.strip() == '---':
                story.append(Spacer(1, 0.1*inch))
            
            # Checkboxes
            elif '- [ ]' in line or '- [x]' in line:
                text = line.replace('- [ ]', '☐').replace('- [x]', '☑')
                story.append(Paragraph(text, styles['Normal']))
            
            # Bullet points
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                text = line.strip()[2:]
                story.append(Paragraph('• ' + text, styles['Normal']))
            
            # Blockquotes
            elif line.strip().startswith('>'):
                text = line.strip()[1:].strip()
                if text:
                    story.append(Paragraph('<i>' + text + '</i>', styles['Normal']))
            
            # Regular paragraphs
            elif line.strip():
                # Handle bold
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                # Handle italic
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                # Remove emojis and special characters that cause issues
                text = re.sub(r'[^\x00-\x7F]+', '', text)
                story.append(Paragraph(text, styles['Normal']))
            
            # Empty lines
            else:
                story.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        pdf.build(story)
        return True
    except Exception as e:
        print(f"Error converting {md_file}: {e}")
        return False

# Find all markdown files
md_files = []

# Root directory
md_files.extend(glob.glob('*.md'))

# Docs directory
md_files.extend(glob.glob('docs/*.md'))

print(f"Found {len(md_files)} markdown files")
print("=" * 60)

converted = 0
failed = 0

for md_file in md_files:
    # Skip if PDF already exists and is newer
    pdf_file = md_file.replace('.md', '.pdf')
    
    print(f"Converting: {md_file}")
    
    if convert_md_to_pdf(md_file, pdf_file):
        print(f"  ✓ Created: {pdf_file}")
        converted += 1
    else:
        print(f"  ✗ Failed: {md_file}")
        failed += 1
    print()

print("=" * 60)
print(f"Conversion complete!")
print(f"  Converted: {converted}")
print(f"  Failed: {failed}")
print(f"  Total: {len(md_files)}")
