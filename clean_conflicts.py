import os
import re

def clean_file(path):
    print(f"Checking {path}...")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return

    new_lines = []
    # Marcadores de conflito do Git
    marker_start = re.compile(r'^<<<<<<< .*')
    marker_mid   = re.compile(r'^=======')
    marker_end   = re.compile(r'^>>>>>>> .*')

    skip = False
    modified = False

    for line in lines:
        sline = line.strip()
        if marker_start.match(sline):
            skip = False # Manter o lado HEAD (geralmente o primeiro bloco)
            modified = True
            continue
        if marker_mid.match(sline):
            skip = True  # Pular o lado remoto
            modified = True
            continue
        if marker_end.match(sline):
            skip = False
            modified = True
            continue
        
        if not skip:
            new_lines.append(line)

    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"Fixed conflicts in {path}")

def walk_and_clean(directory):
    for root, dirs, files in os.walk(directory):
        # Pular pastas irrelevantes
        if '.gemini' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                clean_file(os.path.join(root, file))

if __name__ == "__main__":
    # Limpa tanto a pasta Game quanto a pasta Menu
    walk_and_clean(".")
