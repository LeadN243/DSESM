import json

# Load notebook
with open('groupQasssignment.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

# Find and fix the problematic code
modified = False
for cell_idx, cell in enumerate(nb['cells']):
    if cell.get('cell_type') == 'code':
        source = ''.join(cell.get('source', []))
        
        # Fix 1: Remove 'network': n_scenario from scenario_results
        if "'network': n_scenario," in source:
            print(f"Found network assignment in cell {cell_idx}")
            new_source = source.replace(
                "                    'network': n_scenario,\n",
                ""
            )
            cell['source'] = new_source.splitlines(keepends=True)
            modified = True
            print(f"  ✅ Removed 'network': n_scenario assignment")

# Save modified notebook
if modified:
    with open('groupQasssignment.ipynb', 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print("\n✅ Notebook fixed and saved!")
else:
    print("No modifications needed")
