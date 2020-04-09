import json
import sys
from joblib import Parallel, delayed
from itertools import product
import argparse
import pandas as pd
import os
import numpy as np
import random

# parser = argparse.ArgumentParser()
# parser.add_argument('-q', dest='qps', nargs='+', type=int, required=True)
# parser.add_argument('-f', dest='folder', type=int, required=True)
# parser.add_argument('-m', dest='mode', type=str, required=True)
# args = parser.parse_args()

# qps = args.qps
# folder = args.folder
# mode = args.mode 

qps = 200
model = "grpc"

log_dir = "/home/ml2585/filers/ath-9/dependency/three_tier_" + model + "/"

iter_num = 5
service_num = 2
iter_list = [1]
interfere = 1
if_cnt = True

span_names = [
    "rpc_0_server",
    "rpc_1_client",
    "rpc_1_server",
    "rpc_2_client",
    "rpc_2_server",
    "rpc_3_client",
    "rpc_3_server",
    "rpc_4_client",
    "rpc_4_server",
    "rpc_5_client",
    "rpc_5_server",
    "rpc_6_client",
    "rpc_6_server",
]

# if model == "grpc":
#   n_spans = 7
# else:
#   n_spans = 10

def gen_df(i, q):
  filename = log_dir + "qps_" + str(q)+ "/0_10/iter_" + str(i) + ".csv"
  with open(filename, 'r') as f:
    df = pd.read_csv(f)
    print(filename)

    # Filter out traces with incomplete spans
    count_df = df[['traceID', 'startTime']].groupby(['traceID'], as_index=False).count()
    count_df.columns = ['traceID', 'count']

    # count_df = count_df[count_df['count'] == n_spans]
    df = df.merge(count_df, on='traceID', how='inner')[['traceID', 'operationName', 'duration', 'startTime']]

    duration_df = pd.pivot_table(df[['traceID', 'operationName', 'duration']], index='traceID', columns='operationName', values='duration')[span_names]

    tmp_df = pd.pivot_table(df[['traceID', 'operationName', 'duration', 'startTime']], index='traceID', columns='operationName', values='startTime')[span_names]

    for span in span_names:
      tmp_df[span] = pd.to_datetime(tmp_df[span], unit='us')

    server_dfs = []
    for span in span_names:
      server_df = df[df["operationName"] == span]
      server_df["startTime"] = pd.to_datetime(server_df["startTime"], unit='us')
      grouper = server_df.groupby(pd.Grouper(key='startTime', freq='0.1S'))
      if if_cnt:
        tmp_df = grouper['duration'].count().to_frame()
      else:
        tmp_df = grouper['duration'].quantile(99 / 100).to_frame()
      tmp_df.rename(columns={"duration":span}, inplace=True)
      server_dfs.append(tmp_df)

    # print(server_dfs)
    servers_df = server_dfs[0]
    for tmp_df in server_dfs[1:]:
      servers_df = servers_df.merge(tmp_df, on="startTime", how='inner')
    
    print(servers_df)
    return servers_df

dfs = []

tmp_dfs = Parallel(n_jobs=2)(delayed(gen_df) (i, qps) for i in iter_list)
for i in tmp_dfs:
  dfs.append(i)

df = pd.concat(dfs, ignore_index=True)

print(df)

with open("./results/latency_tmp.csv", 'w') as f:
    df.to_csv(f)


