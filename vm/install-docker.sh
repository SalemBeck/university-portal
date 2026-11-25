#!/usr/bin/env bash
# Install Docker Engine + Compose plugin on Ubuntu 24.04 (official Docker apt repo).
# Run inside the VM:  bash vm/install-docker.sh
set -euo pipefail

sudo apt-get update
sudo apt-get install -y ca-certificates curl git htop
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"     # run docker without sudo (re-login needed)
sudo systemctl enable --now docker
docker --version && docker compose version
