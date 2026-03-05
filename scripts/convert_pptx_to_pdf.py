"""
Convert PowerPoint presentations to PDF
Requires Microsoft PowerPoint installed on Windows
"""

import os
import glob

try:
    import win32com.client
    
    def convert_pptx_to_pdf(pptx_path, pdf_path):
        """Convert a PowerPoint file to PDF"""
        try:
            # Create PowerPoint application object
            powerpoint = win32com.client.Dispatch("PowerPoint.Application")
            powerpoint.Visible = 1
            
            # Open the presentation
            presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False)
            
            # Save as PDF
            presentation.SaveAs(pdf_path, 32)  # 32 = ppSaveAsPDF
            
            # Close presentation
            presentation.Close()
            
            return True
        except Exception as e:
            print(f"Error converting {pptx_path}: {e}")
            return False
        finally:
            try:
                powerpoint.Quit()
            except:
                pass
    
    # Find all PowerPoint files in presentations folder
    pptx_files = glob.glob('presentations/*.pptx')
    
    print(f"Found {len(pptx_files)} PowerPoint files")
    print("=" * 60)
    
    converted = 0
    failed = 0
    
    for pptx_file in pptx_files:
        # Get absolute paths
        abs_pptx = os.path.abspath(pptx_file)
        pdf_file = pptx_file.replace('.pptx', '.pdf')
        abs_pdf = os.path.abspath(pdf_file)
        
        print(f"Converting: {pptx_file}")
        
        if convert_pptx_to_pdf(abs_pptx, abs_pdf):
            print(f"  ✓ Created: {pdf_file}")
            converted += 1
        else:
            print(f"  ✗ Failed: {pptx_file}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Conversion complete!")
    print(f"  Converted: {converted}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(pptx_files)}")

except ImportError:
    print("ERROR: win32com module not found!")
    print()
    print("To install, run:")
    print("  pip install pywin32")
    print()
    print("Alternative: Open PowerPoint files manually and use 'Save As' → PDF")
