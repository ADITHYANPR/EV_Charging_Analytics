import pymupdf
import re

doc = pymupdf.open('EV_Charging_Analytics_Case_Study_Final_Draft.pdf')

def find_first_page(title):
    # Normalize
    t = title.strip().split(':')[0] # handle Table 1: etc
    for pno in range(3, len(doc)):
        text = doc[pno].get_text()
        if t in text:
            return pno + 1
    return '??'

with open('build_final_case_study.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Extract toc_items list
start = code.find('toc_items = [')
end = code.find('    t_toc = doc.add_table')
toc_block = code[start:end]

# Evaluate toc_items
namespace = {}
exec(toc_block, namespace)
toc_items = namespace['toc_items']

print("=== ACTUAL TOC PAGE MAPPING ===")
for sec_title, p_num, subitems in toc_items:
    act_p = find_first_page(sec_title)
    print(f'("{sec_title}", "{act_p}", [')
    for sub_title, sub_p in subitems:
        act_sp = find_first_page(sub_title)
        print(f'    ("{sub_title}", "{act_sp}"),')
    print(']),')
