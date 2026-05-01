import zipfile, re

with zipfile.ZipFile('AICS_REPORT SUBMISSION-template.docx', 'r') as z:
    xml_data = z.read('word/document.xml').decode('utf-8')

paras = re.findall(r'<w:p[^>]*>(.*?)</w:p>', xml_data, re.DOTALL)
count = 0
with open('template_structure.txt', 'w', encoding='utf-8') as f:
    for i, para in enumerate(paras):
        texts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', para)
        line = ''.join(texts).strip()
        if line and len(line) > 2:
            style_match = re.search(r'<w:pStyle\s+w:val="([^"]+)"', para)
            style = style_match.group(1) if style_match else 'body'
            f.write(f'[{i}] ({style}) {line[:250]}\n')
            count += 1
            if count > 60:
                break
