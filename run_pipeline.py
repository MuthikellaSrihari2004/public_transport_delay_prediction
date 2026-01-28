
import os
import sys
import subprocess
import time

def run_command(cmd):
    print(f"🚀 Running: {cmd}")
    start = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end = time.time()
    if result.returncode == 0:
        print(f"✅ Success ({end-start:.2f}s)")
        print(result.stdout[:500] if result.stdout else "") # Show snippet
        return True
    else:
        print(f"❌ Failed ({end-start:.2f}s)")
        print(result.stdout)
        print(result.stderr)
        return False

def main():
    steps = [
        "python src/data/make_dataset.py",
        "python src/data/clean_data.py",
        "python src/data/build_features.py",
        "python create_deploy_db.py"
    ]
    
    for step in steps:
        if not run_command(step):
            break
    
    print("\n🏁 Pipeline complete.")

if __name__ == "__main__":
    main()
