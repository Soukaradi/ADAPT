import os
import sys

print("=" * 70)
print("DIAGNOSTIC SCRIPT")
print("=" * 70)
print()

print(f"Current directory: {os.getcwd()}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")
print()

print("Files in current directory:")
print("-" * 70)
files = os.listdir('.')
py_files = [f for f in files if f.endswith('.py')]
for f in sorted(py_files):
    size = os.path.getsize(f)
    print(f"  {f:<30} ({size:,} bytes)")
print()

print("Checking analytics.py content:")
print("-" * 70)
if 'analytics.py' in files:
    with open('analytics.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()[:20]  # First 20 lines
        for i, line in enumerate(lines, 1):
            print(f"  {i:3}: {line.rstrip()}")
    print("  ...")
    print(f"  Total lines: {len(lines)}")
else:
    print("  [ERROR] analytics.py NOT FOUND!")
print()

print("Checking for relative imports in analytics.py:")
print("-" * 70)
if 'analytics.py' in files:
    with open('analytics.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'from .' in content:
            print("  [ERROR] Found relative imports!")
            for i, line in enumerate(content.split('\n'), 1):
                if 'from .' in line:
                    print(f"    Line {i}: {line.strip()}")
        else:
            print("  [OK] No relative imports found")
print()

print("Testing direct import:")
print("-" * 70)
try:
    sys.path.insert(0, os.getcwd())
    import analytics
    print("  [SUCCESS] analytics imported!")
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()