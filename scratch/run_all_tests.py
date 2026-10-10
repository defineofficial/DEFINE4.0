import subprocess
import sys

res = subprocess.run([sys.executable, "-m", "pytest", "api/tests"], capture_output=True, text=True)
with open(r"c:\Users\giris\Desktop\projects\DEFINE\DEFINE4.0_Untitled-5-\test_results.txt", "w", encoding="utf-8") as f:
    f.write(res.stdout)
    if res.stderr:
        f.write("\nSTDERR:\n")
        f.write(res.stderr)
    f.write(f"\nExit code: {res.returncode}\n")
print("Written!")
