import json

with open('groupQasssignment.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Check line 6401
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        src = ''.join(cell['source'])
        if 'if r' in src and 'status' in src:
            # Find the line
            for j, line in enumerate(cell['source']):
                if "if r['status']" in line:
                    print(f"Cell {i}, line {j}: {line.strip()}")
