import os;
import sys;
import subprocess;
import time;
import threading;

if len(sys.argv)<4:
    print("Usage python monitor.py CORES TIME NAME (OUTPUT_DIR)")

# os.system("killall perf")

PROCESS = sys.argv[1]
TIME = int(sys.argv[2])
NAME = sys.argv[3]
if len(sys.argv)>4:
    DIR = sys.argv[4]
else:
    DIR = os.getcwd()

PERF_EXE = "/home/sc2682/bin/perf"

perfout = open("%s/%s_proc.perf" % ( DIR, NAME), "w")

perfproc = subprocess.Popen("%s stat -e instructions,cycles,branch-misses,cache-misses,context-switches -I 1000 -p $(pgrep -x %s) -g sleep %d" % (PERF_EXE, PROCESS, TIME/2), shell=True, stdout=perfout, stderr=perfout, preexec_fn=os.setsid)
perfproc.wait()

perfout.close()

