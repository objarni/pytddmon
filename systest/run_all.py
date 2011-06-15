import os
import shutil
import glob
import subprocess

def run_all():
    shutil.copy("../pyTDDmon.pyw", ".")
    for systest_file in glob.glob("systest_*.py"):
        print(systest_file)
        subprocess.call(['python', systest_file])
    os.unlink("pyTDDmon.pyw")


if __name__ == "__main__":
    run_all()
    