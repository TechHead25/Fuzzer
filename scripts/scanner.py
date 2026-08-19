import os
import re

search_dirs = [
    r"c:\Projects\Fuzzer\backend",
    r"c:\Projects\Fuzzer\frontend",
    r"c:\Projects\Fuzzer\scripts",
    r"c:\Projects\Fuzzer\worker"
]

credential_pattern = re.compile(r'(?i)(password|secret|api_key|token)\s*=\s*[\'"][^\'"]+[\'"]')
path_pattern = re.compile(r'C:\\Users\\[^\\]+|C:\\Projects\\[^\\]+')
mock_pattern = re.compile(r'(?i)(mock|fake|dummy|simulate)')
todo_pattern = re.compile(r'(?i)(TODO|FIXME|XXX)')

def scan():
    for d in search_dirs:
        for root, _, files in os.walk(d):
            if 'venv' in root or 'node_modules' in root or '.next' in root or '__pycache__' in root:
                continue
            for file in files:
                if not file.endswith(('.py', '.ts', '.tsx', '.md')): continue
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                except:
                    continue
                
                for i, line in enumerate(lines):
                    if credential_pattern.search(line):
                        print(f"[CREDENTIAL] {filepath}:{i+1} -> {line.strip()}")
                    if path_pattern.search(line) and "c:\\Projects\\Fuzzer" not in line.lower():
                        print(f"[PATH] {filepath}:{i+1} -> {line.strip()}")
                    if mock_pattern.search(line):
                        print(f"[MOCK] {filepath}:{i+1} -> {line.strip()}")
                    if todo_pattern.search(line):
                        print(f"[TODO] {filepath}:{i+1} -> {line.strip()}")

if __name__ == '__main__':
    scan()
