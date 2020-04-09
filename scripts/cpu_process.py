import json
import sys
from joblib import Parallel, delayed
from itertools import product
import argparse
import pandas as pd
import os
import numpy as np
import random
import matplotlib.pyplot as plt

# parser = argparse.ArgumentParser()
# parser.add_argument('-q', dest='qps', nargs='+', type=int, required=True)
# parser.add_argument('-f', dest='folder', type=int, required=True)
# parser.add_argument('-m', dest='mode', type=str, required=True)
# args = parser.parse_args()

# qps = args.qps
# folder = args.folder
# mode = args.mode 
qps = 100

model = "grpc"

log_dir = "/home/ml2585/filers/ath-9/dependency/five_tier_grpc/qps_100/0_10"

iter_num = 5
n_services = [0,1,2,3,4,5,6]

interfere = 0
level = 10

span_names = [
    "rpc_0_server",
    "rpc_1_client",
    "rpc_1_server",
    "rpc_2_client",
    "rpc_2_server",
    "rpc_3_client",
    "rpc_3_server",
]

# iter_list = list([file_id])
# iter_list = [i for i in range(0, 5)]
iter_list = [i for i in range(0,10)]

n_spans = 10

def gen_df(i, q):
  filename = log_dir + "/metrics_" + str(i) + ".csv"
  with open(filename, 'r') as f:
    df = pd.read_csv(f)
    total_record = int(df.shape[0] / len(n_services))
    df = df[['name', 'core_util', 'cpu_util', 'timestamp']]
    dfs_dict = {}
    tmp_dict = {}
    for i in n_services:
      tmp_df = df[df['name'] == ('service_' + str(i))]
      tmp_df_core = tmp_df.reset_index()["core_util"]
      tmp_df_cpu = tmp_df.reset_index()["cpu_util"]
      tmp_df_time = tmp_df.reset_index()["timestamp"]
      dfs_dict['service_' + str(i) + '_core'] = tmp_df_core
      dfs_dict['service_' + str(i) + '_cpu'] = tmp_df_cpu
      tmp_dict['service_' + str(i) + '_time'] = tmp_df_time

    # for i in n_services:
    #   plt.figure(1)
    #   core_data = dfs_dict['service_' + str(i) + '_core'].tolist()[:-1]
    #   time_data = tmp_dict['service_' + str(i) + '_time'].tolist()[:-1]
    #   x = [ t - time_data[0] for t in time_data]
    #   plt.plot(x, core_data, label="service_" + str(i) + "_core")
    #   plt.ylim(0, 100)
    #   plt.legend(loc='upper left', bbox_to_anchor=(0, 0.95))
    #   plt.savefig("./core.png", dpi=120)
    #   plt.title("core")

    #   plt.figure(2)
    #   cpu_data = dfs_dict['service_' + str(i) + '_cpu'].tolist()[:-1]
    #   plt.plot(x, cpu_data, label="service_" + str(i) + "_cpu")
    #   plt.ylim(0, 100)
    #   plt.legend(loc='upper left', bbox_to_anchor=(0, 0.9))
    #   plt.savefig("./cpu.png", dpi=120)
    #   plt.title("cpu")

    dfs = pd.DataFrame(dfs_dict)
    # print(dfs)
    # return dfs
    interfered_index = dfs[dfs["service_0_core"] > 90].index.tolist()
    normal_index = [j for j in range(total_record)]
    for j in interfered_index:
      if j in normal_index:
        normal_index.remove(j)
    normal_index.remove(min(interfered_index) - 1)
    normal_index.remove(max(interfered_index) + 1)
    interfered_index.remove(max(interfered_index))

    # print(interfered_index)
    # print(normal_index)
    # print(dfs.iloc[interfered_index, :].mean())
    # print(dfs.iloc[normal_index, :].mean())

    interfered_df = dfs.iloc[interfered_index, :].mean().to_frame().T
    interfered_df.columns = [j + "_interfered" for j in interfered_df.columns]
    normal_df = dfs.iloc[normal_index, :].mean().to_frame().T
    normal_df.columns = [j + "_normal" for j in normal_df.columns]

    for column in normal_df.columns:
      interfered_df[column] = normal_df[column]
    
    # print(pd.DataFrame(dfs_dict))
    for column in interfered_df.columns:
      interfered_df[column] = interfered_df[column].round(2)
    # print(interfered_df)

    return interfered_df

dfs = []

tmp_dfs = Parallel(n_jobs=2)(delayed(gen_df) (i, qps) for i in iter_list)
for i in tmp_dfs:
  dfs.append(i)

df = pd.concat(dfs, ignore_index=True)

mean_df = df.mean().to_frame().T

df = pd.concat([df,mean_df], axis = 0, ignore_index=True)

for column in df.columns:
  df[column] = df[column].round(2)

print(df)

with open("./results/cpu_tmp.csv", 'w') as f:
  df.to_csv(f)
