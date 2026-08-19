import os

def fix_use_client(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        use_client_idx = -1
        for i, line in enumerate(lines):
            if '"use client"' in line or "'use client'" in line:
                use_client_idx = i
                break
                
        if use_client_idx > 0:
            use_client_line = lines.pop(use_client_idx)
            lines.insert(0, use_client_line)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f'Fixed {filepath}')
    except Exception as e:
        print(f'Error on {filepath}: {e}')

for root, _, files in os.walk('src/app'):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            fix_use_client(os.path.join(root, file))
