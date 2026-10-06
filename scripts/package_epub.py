#!/usr/bin/env python3
"""
package_epub.py
Packages an EPUB build directory into a standard .epub file:
- mimetype stored uncompressed as the first entry
- META-INF and OEBPS files compressed with DEFLATED
"""

import sys, os, zipfile

def package_epub(build_dir, output_epub_path):
    if not os.path.exists(build_dir):
        print(f"Error: Build dir does not exist: {build_dir}")
        sys.exit(1)
        
    mimetype_path = os.path.join(build_dir, "mimetype")
    if not os.path.exists(mimetype_path):
        with open(mimetype_path, "w", encoding="utf-8") as f:
            f.write("application/epub+zip")
            
    os.makedirs(os.path.dirname(os.path.abspath(output_epub_path)), exist_ok=True)
    if os.path.exists(output_epub_path):
        os.remove(output_epub_path)
        
    with zipfile.ZipFile(output_epub_path, 'w') as zf:
        # 1. mimetype (first, uncompressed)
        zf.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
        
        # 2. META-INF/container.xml
        meta_inf = os.path.join(build_dir, "META-INF", "container.xml")
        if os.path.exists(meta_inf):
            zf.write(meta_inf, "META-INF/container.xml", compress_type=zipfile.ZIP_DEFLATED)
            
        # 3. OEBPS files
        oebps_dir = os.path.join(build_dir, "OEBPS")
        if os.path.exists(oebps_dir):
            for root, dirs, files in os.walk(oebps_dir):
                for f in sorted(files):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, build_dir)
                    zf.write(full_p, rel_p, compress_type=zipfile.ZIP_DEFLATED)
                    
    size_mb = os.path.getsize(output_epub_path) / (1024 * 1024)
    print(f"[✓] Packaged {output_epub_path} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: package_epub.py <build_dir> <output.epub>")
        sys.exit(1)
    package_epub(sys.argv[1], sys.argv[2])
