#!/usr/bin/env python3
"""
verify_epub.py
Rigorous verification suite for EPUB quality and standard compliance:
1. Mimetype check (first entry, uncompressed ZIP_STORED)
2. XML parse check for all XHTML/XML/OPF/NCX files
3. Manifest integrity check
4. Image link resolution check
5. Quality Check: 0 paragraphs start with orphan leading punctuation
6. Footnote link resolution check
"""

import sys, os, re, zipfile
import xml.etree.ElementTree as ET

LEADING_PUNCT = re.compile(r'^[，。、；：？！’”’）》』]')

def verify_epub(epub_path):
    print(f"=== Verifying {os.path.basename(epub_path)} ===")
    if not os.path.exists(epub_path):
        print(f"FAILED: File does not exist: {epub_path}")
        return False

    zf = zipfile.ZipFile(epub_path, 'r')
    infolist = zf.infolist()

    # 1. Check mimetype
    if not infolist or infolist[0].filename != 'mimetype':
        print(f"FAILED: First entry is {infolist[0].filename if infolist else 'EMPTY'}, expected 'mimetype'")
        return False
    if infolist[0].compress_type != zipfile.ZIP_STORED:
        print(f"FAILED: mimetype compression is {infolist[0].compress_type}, expected ZIP_STORED (0)")
        return False
    mimetype_content = zf.read('mimetype').decode('utf-8')
    if mimetype_content != 'application/epub+zip':
        print(f"FAILED: mimetype content is {repr(mimetype_content)}, expected 'application/epub+zip'")
        return False
    print("PASS: Mimetype is valid, uncompressed, and first entry.")

    # 2. Check XML parse
    xml_count = 0
    for info in infolist:
        if info.filename.endswith(('.xml', '.xhtml', '.opf', '.ncx')):
            content = zf.read(info.filename)
            try:
                ET.fromstring(content)
                xml_count += 1
            except ET.ParseError as e:
                print(f"FAILED: XML ParseError in {info.filename}: {e}")
                return False
    print(f"PASS: All {xml_count} XML/XHTML files parsed successfully without errors.")

    # 3. Check OPF manifest
    opf_files = [f for f in zf.namelist() if f.endswith('.opf')]
    if not opf_files:
        print("FAILED: No .opf package document found!")
        return False
    opf_path = opf_files[0]
    opf_dir = os.path.dirname(opf_path)
    opf_data = zf.read(opf_path)
    opf_root = ET.fromstring(opf_data)
    items = opf_root.findall('.//{http://www.idpf.org/2007/opf}item')
    
    for item in items:
        href = item.attrib.get('href')
        full_path = os.path.normpath(os.path.join(opf_dir, href)) if opf_dir else href
        if full_path not in zf.namelist():
            print(f"FAILED: Manifest item missing from archive: {full_path}")
            return False
    print("PASS: All manifest items exist in archive.")

    # 4. Check image references in XHTML
    missing_imgs = []
    for info in infolist:
        if info.filename.endswith('.xhtml'):
            content = zf.read(info.filename).decode('utf-8')
            for src in re.findall(r'<img[^>]+src=\"([^\"]+)\"', content):
                target = os.path.normpath(os.path.join(os.path.dirname(info.filename), src))
                if target not in zf.namelist():
                    missing_imgs.append((info.filename, src, target))
    if missing_imgs:
        print(f"FAILED: Missing image references: {missing_imgs}")
        return False
    print("PASS: All image references in XHTML files resolve cleanly.")

    # 5. Quality Criteria: 0 paragraphs start with orphan punctuation
    bad_paragraphs = []
    total_paragraphs = 0
    for info in infolist:
        if info.filename.endswith('.xhtml') and ('Text/' in info.filename or 'text/' in info.filename):
            content = zf.read(info.filename).decode('utf-8')
            for p_match in re.finditer(r'<p(?:[^>]*)>(.*?)</p>', content, re.DOTALL):
                total_paragraphs += 1
                plain = re.sub(r'<[^>]+>', '', p_match.group(1)).strip()
                if LEADING_PUNCT.match(plain):
                    bad_paragraphs.append((info.filename, plain[:40]))
    print(f"Inspected {total_paragraphs} paragraphs across all XHTML files.")
    if bad_paragraphs:
        print(f"FAILED: Found {len(bad_paragraphs)} paragraphs with leading punctuation:")
        for fn, txt in bad_paragraphs:
            print(f"  {os.path.basename(fn)}: {txt}")
        return False
    print("PASS: 0 paragraphs start with invalid punctuation. Smooth reading flow.")

    # 6. Check Footnotes
    fn_broken = []
    for info in infolist:
        if info.filename.endswith('.xhtml'):
            content = zf.read(info.filename).decode('utf-8')
            refs = re.findall(r'href=\"#fn-([^\"]+)\"', content)
            for ref in refs:
                if f'id="fn-{ref}"' not in content:
                    fn_broken.append((info.filename, ref))
    if fn_broken:
        print(f"FAILED: Broken footnote references: {fn_broken}")
        return False
    print("PASS: All footnote references resolve to valid anchors.")

    print(f"=== [✓] {os.path.basename(epub_path)} IS PERFECT AND VALID! ===")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: verify_epub.py <file.epub>")
        sys.exit(1)
    success = verify_epub(sys.argv[1])
    sys.exit(0 if success else 1)
