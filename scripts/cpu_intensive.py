import time
import argparse
import random

parser = argparse.ArgumentParser()
parser.add_argument('-i', dest='intensity', type=int, required=True)
parser.add_argument('-d', dest='duration', type=int, required=True)
args = parser.parse_args()

intensity = args.intensity
duration = args.duration

def worker(run_flag):
  if run_flag:
    i = 0
    start_ts = int(time.time() * 1000)
    while (int(time.time() * 1000) - start_ts) <= 10:
      i += 1
  else:
    time.sleep(1e-2)

start_ts = int(time.time() * 1000)
end_ts = start_ts + duration * 1e3

i = 0
while (int(time.time() * 1000) <= end_ts):
  run_flag = random.randint(1, 10) <= intensity
  worker(run_flag)