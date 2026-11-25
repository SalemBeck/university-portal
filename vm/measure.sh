#!/usr/bin/env bash
# Part B - observe resources with containers idle and under a small HTTP load
echo "== Idle with containers"; free -m | grep Mem; uptime
sudo docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo "== Load: 2000 requests, 20 in parallel"
start=$(date +%s)
( seq 2000 | xargs -P 20 -I{} curl -s -o /dev/null http://localhost:8080/announcements ) &
sleep 6
sudo docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
top -bn1 | head -5 | tail -3
free -m | grep Mem
wait
echo "duration: $(( $(date +%s) - start )) s"
uptime
