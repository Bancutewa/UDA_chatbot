
import os
import ast
import sys

def get_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read(), filename=file_path)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])
    return imports

def scan_project(root_dir):
    all_imports = set()
    for root, dirs, files in os.walk(root_dir):
        if 'venv' in root or '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                imports = get_imports(file_path)
                all_imports.update(imports)
    return all_imports

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.abspath(__file__))
    used_imports = scan_project(root_dir)
    print("Detected Imports:")
    for imp in sorted(used_imports):
        print(imp)
