#!/usr/bin/env bash
# Part B - inspect the VM: OS, resources, network
echo "== hostnamectl";  hostnamectl | grep -E "Static hostname|Operating System|Kernel|Virtualization|Hardware"
echo "== CPU";          lscpu | grep -E "^CPU\(s\)|Model name|Hypervisor"
echo "== Memory";       free -h
echo "== Disk";         df -h / ; lsblk -d -o NAME,SIZE,TYPE | grep disk
echo "== Network";      ip -br addr
echo "== Load";         uptime
