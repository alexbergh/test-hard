import re
import sys

path = sys.argv[1]
with open(path) as fh:
    lines = fh.readlines()
new_lines = []
inserted = False
for line in lines:
    new_lines.append(line)
    if not inserted and re.match(r"\s+-\s+kube-(apiserver|controller-manager|scheduler)\s*$", line):
        m = re.match(r"^(\s+)", line)
        indent = m.group(1) if m else "    "
        new_lines.append(indent + "- --profiling=false\n")
        inserted = True
if not inserted:
    new_lines2 = []
    for line in lines:
        new_lines2.append(line)
        if not inserted and "command:" in line:
            new_lines2.append("    - --profiling=false\n")
            inserted = True
    new_lines = new_lines2
with open(path, "w") as fh:
    fh.writelines(new_lines)
print("DONE " + path)
