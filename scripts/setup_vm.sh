#!/usr/bin/env bash
# ==============================================================================
# Cortex Cloud Server Automated Setup Script (Ubuntu ARM64 / x86_64)
# ==============================================================================
set -euo pipefail

echo "================================================================"
echo " Starting Cortex Cloud Server Setup"
echo " OS: $(lsb_release -d 2>/dev/null || uname -s)"
echo " Architecture: $(uname -m)"
echo "================================================================"

# 1. Update and install prerequisites
echo "[1/6] Updating system packages..."
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release ufw git

# 2. Configure 4GB Swapfile for memory resilience (prevents OOM on free VMs)
if [ ! -f /swapfile ]; then
    echo "[2/6] Configuring 4GB swap space for memory resilience..."
    sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    # Optimize swappiness for server workloads
    sudo sysctl vm.swappiness=10
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
else
    echo "[2/6] Swap space already exists. Skipping."
fi

# 3. Install official Docker Engine & Docker Compose plugin
if ! command -v docker &> /dev/null; then
    echo "[3/6] Installing official Docker Engine..."
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Enable and start Docker service
    sudo systemctl enable docker
    sudo systemctl start docker

    # Add current user to docker group (avoids needing sudo for docker commands)
    sudo usermod -aG docker "$USER"
    echo "Docker installed successfully."
else
    echo "[3/6] Docker already installed. Skipping."
fi

# 4. Configure UFW Firewall (Principle of Least Privilege)
echo "[4/6] Configuring firewall (UFW)..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP Web'
sudo ufw allow 443/tcp comment 'HTTPS Web'
# Note: PostgreSQL (5432) and Redis (6379) are explicitly NOT allowed
echo "y" | sudo ufw enable

# 5. Fix OCI iptables default rule (Oracle Ubuntu images default to DROP in iptables)
if sudo iptables -L INPUT -n | grep -q "REJECT"; then
    echo "Adjusting Oracle Linux default iptables reject rules to permit Docker traffic..."
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT || true
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT || true
    if command -v netfilter-persistent &> /dev/null; then
        sudo netfilter-persistent save || true
    fi
fi

# 6. Install cloudflared (Cloudflare Tunnel CLI for free zero-port HTTPS)
if ! command -v cloudflared &> /dev/null; then
    echo "[5/6] Installing cloudflared..."
    ARCH=$(dpkg --print-architecture)
    if [ "$ARCH" = "arm64" ]; then
        curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb -o /tmp/cloudflared.deb
    else
        curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb
    fi
    sudo dpkg -i /tmp/cloudflared.deb || sudo apt-get install -f -y
    rm -f /tmp/cloudflared.deb
    echo "cloudflared installed."
else
    echo "[5/6] cloudflared already installed."
fi

echo "[6/6] Server environment preparation complete!"
echo "Please run: newgrp docker (or log out and log back in) to apply docker permissions."

