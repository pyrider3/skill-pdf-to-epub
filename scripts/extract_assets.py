#!/usr/bin/env python3
"""
extract_assets.py
Extracts assets from a PDF for EPUB conversion:
1. Cover image rendering (Page 1 at 300 DPI) via pdftoppm
2. Embedded raster images via pdfimages -png
3. High-precision coordinate XML via pdftotext -bbox-layout
"""

import sys, os, subprocess, shutil

def extract_pdf_assets(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "Images")
    os.makedirs(images_dir, exist_ok=True)
    
    print(f"[*] Extracting assets from {pdf_path} into {output_dir}")
    
    # 1. Render Cover Page (Page 1) at 300 DPI
    cover_prefix = os.path.join(output_dir, "cover_tmp")
    subprocess.run(["pdftoppm", "-png", "-r", "300", "-f", "1", "-l", "1", pdf_path, cover_prefix], check=True)
    # pdftoppm outputs cover_tmp-1.png or cover_tmp-01.png
    cover_candidates = [f for f in os.listdir(output_dir) if f.startswith("cover_tmp") and f.endswith(".png")]
    if cover_candidates:
        src = os.path.join(output_dir, cover_candidates[0])
        dst = os.path.join(images_dir, "cover.png")
        shutil.move(src, dst)
        print(f"[+] Rendered cover: {dst}")
        
    # 2. Extract embedded images
    img_prefix = os.path.join(output_dir, "raw_img")
    subprocess.run(["pdfimages", "-png", pdf_path, img_prefix], check=True)
    extracted_imgs = [f for f in sorted(os.listdir(output_dir)) if f.startswith("raw_img-") and f.endswith(".png")]
    print(f"[+] Extracted {len(extracted_imgs)} embedded images.")
    for idx, f in enumerate(extracted_imgs):
        src = os.path.join(output_dir, f)
        # Move or rename as needed
        dst = os.path.join(images_dir, f)
        shutil.move(src, dst)
        
    # 3. Extract bbox layout XML
    xml_path = os.path.join(output_dir, "bbox_layout.xml")
    print("[*] Running pdftotext -bbox-layout...")
    res = subprocess.run(["pdftotext", "-bbox-layout", pdf_path, xml_path], check=True)
    print(f"[+] Saved bbox layout to {xml_path} ({os.path.getsize(xml_path)} bytes)")
    print("[✓] Extraction complete!")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: extract_assets.py <input.pdf> <output_dir>")
        sys.exit(1)
    extract_pdf_assets(sys.argv[1], sys.argv[2])
