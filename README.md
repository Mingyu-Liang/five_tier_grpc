# three_tier_grpc

## Prerequisite

### Docker

### Docker Compose

## Usage

```
docker-compose up
```

### Scripts

cpu/perf/latency_process.py: process cpu/perf/latency data

run_perf.py: launch service, launch workload generator(wrk2), launch inferfence and data collection

monitor.py: collect perf data

read_metrics: collect cpu data

cpu_intensive.py: cpu interference
