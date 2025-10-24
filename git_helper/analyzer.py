import re
from collections import Counter

def analyze_diff(diff_text):
    # Parse diff sections
    sections = diff_text.split('\n@@')
    
    # Extract statistics
    additions = []
    deletions = []
    for section in sections:
        if '@@' in section:
            content = section.split('@@')[1]
            for line in content.split('\n'):
                if line.startswith('+ '):
                    additions.append(line[2:])
                elif line.startswith('- '):
                    deletions.append(line[2:])
    
    # Analyze patterns
    addition_patterns = Counter(additions)
    deletion_patterns = Counter(deletions)
    
    return {
        'addition_patterns': dict(addition_patterns),
        'deletion_patterns': dict(deletion_patterns),
        'total_changes': len(additions) + len(deletions)
    }

# Example diff text
sample_diff = """@@ -1,5 +1,7 @@
 class MyClass:
-    def old_method(self):
-        pass
     def __init__(self):
         self.value = 42
+    def new_method(self):
+        return self.value"""

results = analyze_diff(sample_diff)
print("Diff Analysis Results:")
print(f"Total Changes: {results['total_changes']}")
print("\nCommon Additions:", results['addition_patterns'])
print("Common Deletions:", results['deletion_patterns'])
