import json

with open('groupQasssignment.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find cell 50/52 by looking for the section we know
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])
        if 'COMPARISON 1: Baseline vs Zero Emissions' in src:
            print(f"Found comparison cell at index {i}")
            # Find the first status check
            for j, line in enumerate(cell['source']):
                if "if r['status']" in line:
                    print(f"Line {j}: {line.strip()}")
                    break
            break
