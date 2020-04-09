import sys
import os
import subprocess
import threading
from numpy import *
import pandas as pd
import matplotlib.pyplot as plt

FREQ = 2100000

file_dir = sys.argv[1]

latency_dir = file_dir
perf_dir = file_dir + "/perf/"

qps = [ i * 100 for i in range(1, 2, 1)]

def getLatency(filename, qps):
	tail = 0
	avg = 0
	actual_qps = 0
	for line in os.popen("cat " + latency_dir + filename + ".txt").readlines():
		words = line.split()
		if ("Requests/sec" in line):
			actual_qps = float(words[1][:-2])
		elif ("Latency" in line) and ("Distribution" not in line):
			avg = float(words[1][:-2])
		elif ("99.000" in line):
			tail = float(words[1][:-2])

	dic = {}
	dic["qps"] = qps
	dic["actual_qps"] = actual_qps
	dic["avg_latency"] = avg
	dic["99th_latency"] = tail

	df = pd.DataFrame(dic, index=[0])
	return df

def getPerf(filename, qps):
	instrs = []
	cycles = []
	cpi = []
	branch_misses = []
	# LLC_load_misses = []
	# LLC_store_misses = []
	cache_misses = []
	page_faults = []
	context_switches = []
	# print(perf_dir + filename + ".perf")
	with open(perf_dir + filename + "_core.perf", "r") as ff:
		for line in ff.readlines():
			words = line.split()
			if "not counted" in line or "not supported" in line:
				return
			elif "instructions" in line:
				instrs.append(int(words[1].replace(',','')))
			elif "cycles" in line:
				cycles.append(int(words[1].replace(',','')))
			elif "branch-misses" in line:
				branch_misses.append(int(words[1].replace(',','')))
			elif "cache-misses" in line:
				cache_misses.append(int(words[1].replace(',','')))
			elif "page-faults" in line:
				page_faults.append(int(words[1].replace(',','')))
			elif "context-switches" in line:
				context_switches.append(int(words[1].replace(',','')))
			elif "Error" in line: # perf error
				return

	for i in range(len(instrs)):
		cpi.append(cycles[i] / instrs[i])
	# print(cpi)
	dic = {}
	service = filename.split('_')[1]
	interfere_start = int(len(instrs)/3)
	interfere_end = int(len(instrs)/3*2)

	# plt.figure(1)
	# x = range(0, len(instrs))
	# plt.plot(x, instrs, label="service_" + service)
	# plt.legend(loc='upper left', bbox_to_anchor=(0.05, 0.95))
	# plt.title("instrs")
	# plt.savefig("./instrs.png", dpi=120)

	# plt.figure(2)
	# x = range(0, len(cpi))
	# plt.plot(x, cpi, label="service_" + service)
	# plt.legend(loc='upper left', bbox_to_anchor=(0.05, 0.5))
	# plt.title("cpi")
	# plt.savefig("./cpi.png", dpi=120)

	# plt.figure(3)
	# x = range(0, len(cycles))
	# plt.plot(x, cycles, label="service_" + service)
	# plt.legend(loc='upper left', bbox_to_anchor=(0.05, 0.95))
	# plt.title("cycles")
	# plt.savefig("./cycles.png", dpi=120)

	# plt.figure(4)
	# x = range(0, len(context_switches))
	# plt.plot(x, context_switches, label="service_" + service)
	# plt.legend(loc='upper left', bbox_to_anchor=(0.05, 1))
	# plt.title("context_switches")
	# plt.savefig("./context_switches.png", dpi=120)
	# print(instrs)

	# print(len(instrs))
	# dic[service + "_instrs_normal"] = mean(instrs[:interfere_start] + instrs[interfere_end:])
	# dic[service + "_instrs_interfere"] = mean(instrs[interfere_start:interfere_end])
	# dic[service + "_cycles_normal"] = mean(cycles[:interfere_start] + cycles[interfere_end:])
	# dic[service + "_cycles_interfere"] = mean(cycles[interfere_start:interfere_end])
	# dic[service + "_cpi_normal"] = mean(cpi[:interfere_start] + cpi[interfere_end:])
	# dic[service + "_cpi_interfere"] = mean(cpi[interfere_start:interfere_end])
	# dic[service + "_branchm_normal"] = mean(branch_misses[:interfere_start] + branch_misses[interfere_end:])
	# dic[service + "_branchm_interfere"] = mean(branch_misses[interfere_start:interfere_end])
	# dic[service + "_cachem_normal"] = mean(cache_misses[:interfere_start] + cache_misses[interfere_end:])
	# dic[service + "_cachem_interfere"] = mean(cache_misses[interfere_start:interfere_end])
	# dic[service + "_pagefaults_normal"] = mean(page_faults[:interfere_start] + page_faults[interfere_end:])
	# dic[service + "_pagefaults_interfere"] = mean(page_faults[interfere_start:interfere_end])
	# dic[service + "_cs_normal"] = mean(context_switches[:interfere_start] + context_switches[interfere_end:])
	# dic[service + "_cs_interfere"] = mean(context_switches[interfere_start:interfere_end])
	# if service == '5':
	# 	print(context_switches[interfere_start:interfere_end], context_switches[:interfere_start] + context_switches[interfere_end:])
	# 	print(mean(context_switches[interfere_start:interfere_end]), mean(context_switches[:interfere_start] + context_switches[interfere_end:]))

	dic[service + "_instrs"] = (mean(instrs[interfere_start:interfere_end]) - mean(instrs[:interfere_start] + instrs[interfere_end:])) / mean(instrs[:interfere_start] + instrs[interfere_end:])
	dic[service + "_cycles"] = (mean(cycles[interfere_start:interfere_end]) - mean(cycles[:interfere_start] + cycles[interfere_end:])) / mean(cycles[:interfere_start] + cycles[interfere_end:])
	dic[service + "_cpi"] = (mean(cpi[interfere_start:interfere_end]) - mean(cpi[:interfere_start] + cpi[interfere_end:])) / mean(cpi[:interfere_start] + cpi[interfere_end:])
	dic[service + "_branch_misses"] = (mean(branch_misses[interfere_start:interfere_end]) - mean(branch_misses[:interfere_start] + branch_misses[interfere_end:])) / mean(branch_misses[:interfere_start] + branch_misses[interfere_end:])
	# dic[service + "_page_faults"] = (mean(page_faults[interfere_start:interfere_end]) - mean(page_faults[:interfere_start] + page_faults[interfere_end:])) / mean(page_faults[:interfere_start] + page_faults[interfere_end:])
	dic[service + "_context_switches"] = (mean(context_switches[interfere_start:interfere_end]) - mean(context_switches[:interfere_start] + context_switches[interfere_end:])) / mean(context_switches[:interfere_start] + context_switches[interfere_end:])

	# dic["cycles"] = mean(cycles)
	# dic["branch_misses"] = mean(branch_misses)
	# dic["LLC_load_misses"] = mean(LLC_load_misses)
	# dic["LLC_store_misses"] = mean(LLC_store_misses)
	# dic["qps"] = qps

	# actual_qps, avg, tail = getLatency(str(qps))
	# dic["actual_qps"] = actual_qps
	# dic["avg_lat"] = avg
	# dic["99th_lat"] = tail
	# print(dic)
	return dic

	# df = pd.DataFrame(dic, index=[0])

	# return df

dfs = []

n_services = [0,1,2,3,4,5,6]

for q in qps:
	for i in range(10,11):
		dics = []
		for s in n_services:
			dics.append(getPerf(str(i) + "_" + str(s), q))
		dics = [x for x in dics if x!= None]
		dic = dics[0]
		for i in range(1, len(dics)):
			if dics[i] is not None:
				dic = dict(dic, **dics[i])
		df = pd.DataFrame(dic, index=[0])
		# print(df)
		dfs.append(df)

df = pd.concat(dfs, ignore_index=True)
# # df.sort_values(by="qps", axis=0, ascending=True, inplace=True)
# # df.reset_index(inplace=True)

mean_df = df.mean().to_frame().T
# print(mean_df)
df = pd.concat([df, mean_df], axis = 0, ignore_index=True)

for column in df.columns:
  df[column] = df[column].round(4) * 100

columns = []
for s in n_services:
	columns.append(str(s) + "_instrs")
	columns.append(str(s) + "_cycles")
	columns.append(str(s) + "_cpi")
	columns.append(str(s) + "_branch_misses")
	columns.append(str(s) + "_context_switches")
df = df[columns]

print(df)

with open("./results/perf_tmp.csv", 'w') as f:
  df.to_csv(f)