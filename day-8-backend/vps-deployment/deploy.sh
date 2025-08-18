#!/bin/bash

# 🚀 Automated MCP Servers Deployment Script
# Run this script on your VPS to deploy web3-research-mcp and crypto-whitepapers-mcp as HTTPS endpoints

set -e  # Exit on any error

echo "🚀 Starting MCP Servers Deployment..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN_NAME=""
CLOUDFLARE_TUNNEL_TOKEN=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if script is run as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
   exit 1
fi

# Prompt for configuration
echo ""
print_status "Please provide the following information:"
echo ""

if [ -z "$DOMAIN_NAME" ]; then
    read -p "Enter your domain name (e.g., mcp.yourdomain.com): " DOMAIN_NAME
fi

if [ -z "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
    echo ""
    print_warning "To get Cloudflare Tunnel Token:"
    print_warning "1. Go to https://dash.cloudflare.com/"
    print_warning "2. Select your domain"
    print_warning "3. Go to Zero Trust > Access > Tunnels"
    print_warning "4. Create a tunnel, add subdomain '$DOMAIN_NAME'"
    print_warning "5. Copy the tunnel token"
    echo ""
    read -p "Enter your Cloudflare Tunnel Token: " CLOUDFLARE_TUNNEL_TOKEN
fi

echo ""
print_status "Configuration:"
print_status "Domain: $DOMAIN_NAME"
print_status "Tunnel Token: ${CLOUDFLARE_TUNNEL_TOKEN:0:20}..."
echo ""

read -p "Continue with deployment? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Deployment cancelled."
    exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_success "Docker installed successfully"
else
    print_success "Docker already installed"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose already installed"
fi

# Install Node.js
print_status "Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    print_success "Node.js installed successfully"
else
    print_success "Node.js already installed"
fi

# Install Python
print_status "Installing Python..."
if ! command -v python3 &> /dev/null; then
    sudo apt install -y python3 python3-pip
    print_success "Python installed successfully"
else
    print_success "Python already installed"
fi

# Create deployment directory
print_status "Creating deployment directory..."
mkdir -p ~/mcp-deployment
cd ~/mcp-deployment

# Clone MCP repositories
print_status "Cloning MCP repositories..."
if [ ! -d "web3-research-mcp" ]; then
    git clone https://github.com/aaronjmars/web3-research-mcp.git
    cd web3-research-mcp
    npm install
    cd ..
    print_success "web3-research-mcp cloned and installed"
else
    print_success "web3-research-mcp already exists"
fi

if [ ! -d "crypto-whitepapers-mcp" ]; then
    git clone https://github.com/kukapay/crypto-whitepapers-mcp.git
    cd crypto-whitepapers-mcp
    pip3 install -r requirements.txt
    cd ..
    print_success "crypto-whitepapers-mcp cloned and installed"
else
    print_success "crypto-whitepapers-mcp already exists"
fi

# Create HTTP Bridge for web3-research-mcp
print_status "Creating web3-research-mcp HTTP bridge..."
mkdir -p web3-bridge
cat > web3-bridge/server.js << 'EOF'
const express = require('express');
const { spawn } = require('child_process');
const cors = require('cors');

const app = express();
app.use(express.json({ limit: '10mb' }));
app.use(cors());

const PORT = 3001;

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'web3-research-mcp-bridge' });
});

// Tools list endpoint
app.post('/tools/list', async (req, res) => {
    try {
        const mcp = spawn('npx', ['web3-research-mcp'], { 
            stdio: ['pipe', 'pipe', 'pipe'],
            cwd: '/app/web3-research-mcp'
        });

        const request = {
            jsonrpc: '2.0',
            id: 1,
            method: 'tools/list'
        };

        let responseData = '';
        let errorData = '';

        mcp.stdout.on('data', (data) => {
            responseData += data.toString();
        });

        mcp.stderr.on('data', (data) => {
            errorData += data.toString();
        });

        mcp.on('close', (code) => {
            if (code === 0) {
                try {
                    const result = JSON.parse(responseData);
                    res.json(result);
                } catch (e) {
                    res.status(500).json({ error: 'Failed to parse MCP response', details: responseData });
                }
            } else {
                res.status(500).json({ error: 'MCP process failed', code, stderr: errorData });
            }
        });

        mcp.stdin.write(JSON.stringify(request) + '\n');
        mcp.stdin.end();

    } catch (error) {
        res.status(500).json({ error: 'Failed to spawn MCP process', details: error.message });
    }
});

// Tool call endpoint
app.post('/tools/call', async (req, res) => {
    try {
        const { name, arguments: args } = req.body;
        
        const mcp = spawn('npx', ['web3-research-mcp'], { 
            stdio: ['pipe', 'pipe', 'pipe'],
            cwd: '/app/web3-research-mcp'
        });

        const request = {
            jsonrpc: '2.0',
            id: 1,
            method: 'tools/call',
            params: {
                name: name,
                arguments: args || {}
            }
        };

        let responseData = '';
        let errorData = '';

        mcp.stdout.on('data', (data) => {
            responseData += data.toString();
        });

        mcp.stderr.on('data', (data) => {
            errorData += data.toString();
        });

        mcp.on('close', (code) => {
            if (code === 0) {
                try {
                    const result = JSON.parse(responseData);
                    res.json(result);
                } catch (e) {
                    res.status(500).json({ error: 'Failed to parse MCP response', details: responseData });
                }
            } else {
                res.status(500).json({ error: 'MCP process failed', code, stderr: errorData });
            }
        });

        mcp.stdin.write(JSON.stringify(request) + '\n');
        mcp.stdin.end();

    } catch (error) {
        res.status(500).json({ error: 'Failed to spawn MCP process', details: error.message });
    }
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`🌐 Web3 Research MCP Bridge running on port ${PORT}`);
});

process.on('SIGTERM', () => {
    console.log('👋 Shutting down web3 bridge gracefully...');
    process.exit(0);
});
EOF

# Create package.json for web3 bridge
cat > web3-bridge/package.json << 'EOF'
{
  "name": "web3-research-mcp-bridge",
  "version": "1.0.0",
  "description": "HTTP bridge for web3-research-mcp",
  "main": "server.js",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5"
  }
}
EOF

# Create Dockerfile for web3 bridge
cat > web3-bridge/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy and install bridge dependencies
COPY package*.json ./
RUN npm install

# Copy bridge server
COPY server.js ./

# Clone and install web3-research-mcp
RUN apk add --no-cache git
RUN git clone https://github.com/aaronjmars/web3-research-mcp.git
WORKDIR /app/web3-research-mcp
RUN npm install

WORKDIR /app

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

CMD ["npm", "start"]
EOF

# Install bridge dependencies
cd web3-bridge
npm install
cd ..

# Create HTTP Bridge for crypto-whitepapers-mcp
print_status "Creating crypto-whitepapers-mcp HTTP bridge..."
mkdir -p whitepapers-bridge

cat > whitepapers-bridge/server.py << 'EOF'
import json
import subprocess
import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "crypto-whitepapers-mcp-bridge"})

@app.route('/tools/list', methods=['POST'])
def tools_list():
    try:
        # Adjust path to your crypto-whitepapers-mcp installation
        mcp_path = '/app/crypto-whitepapers-mcp'
        
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        result = subprocess.run(
            [sys.executable, '-m', 'crypto_whitepapers_mcp'],
            input=json.dumps(request_data) + '\n',
            capture_output=True,
            text=True,
            cwd=mcp_path,
            timeout=30
        )
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            return jsonify(response)
        else:
            return jsonify({
                "error": "MCP process failed",
                "code": result.returncode,
                "stderr": result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": "Failed to execute MCP",
            "details": str(e)
        }), 500

@app.route('/tools/call', methods=['POST'])
def tools_call():
    try:
        data = request.get_json()
        tool_name = data.get('name')
        tool_args = data.get('arguments', {})
        
        mcp_path = '/app/crypto-whitepapers-mcp'
        
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": tool_args
            }
        }
        
        result = subprocess.run(
            [sys.executable, '-m', 'crypto_whitepapers_mcp'],
            input=json.dumps(request_data) + '\n',
            capture_output=True,
            text=True,
            cwd=mcp_path,
            timeout=60
        )
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            return jsonify(response)
        else:
            return jsonify({
                "error": "MCP process failed", 
                "code": result.returncode,
                "stderr": result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": "Failed to execute MCP",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002, debug=False)
EOF

# Create requirements.txt for whitepapers bridge
cat > whitepapers-bridge/requirements.txt << 'EOF'
Flask==2.3.3
Flask-CORS==4.0.0
requests==2.31.0
EOF

# Create Dockerfile for whitepapers bridge
cat > whitepapers-bridge/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install bridge dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy bridge server
COPY server.py ./

# Clone and install crypto-whitepapers-mcp
RUN git clone https://github.com/kukapay/crypto-whitepapers-mcp.git
WORKDIR /app/crypto-whitepapers-mcp
RUN pip install -r requirements.txt

WORKDIR /app

EXPOSE 3002

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3002/health || exit 1

CMD ["python", "server.py"]
EOF

# Create Docker Compose configuration
print_status "Creating Docker Compose configuration..."
cat > docker-compose.yml << EOF
version: '3.8'

services:
  web3-mcp-bridge:
    build: ./web3-bridge
    container_name: web3-mcp-bridge
    restart: unless-stopped
    ports:
      - "3001:3001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - mcp-network

  whitepapers-mcp-bridge:
    build: ./whitepapers-bridge
    container_name: whitepapers-mcp-bridge
    restart: unless-stopped
    ports:
      - "3002:3002"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - mcp-network

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared-tunnel
    restart: unless-stopped
    command: tunnel --no-autoupdate run --token $CLOUDFLARE_TUNNEL_TOKEN
    networks:
      - mcp-network

networks:
  mcp-network:
    driver: bridge
EOF

# Create systemd service for Docker Compose
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/mcp-deployment.service > /dev/null << EOF
[Unit]
Description=MCP Deployment Services
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$HOME/mcp-deployment
Environment=CLOUDFLARE_TUNNEL_TOKEN=$CLOUDFLARE_TUNNEL_TOKEN
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
print_status "Building and starting MCP services..."
newgrp docker << COMMANDS
docker-compose build
CLOUDFLARE_TUNNEL_TOKEN=$CLOUDFLARE_TUNNEL_TOKEN docker-compose up -d
COMMANDS

# Enable systemd service
sudo systemctl enable mcp-deployment.service
sudo systemctl start mcp-deployment.service

# Wait for services to start
print_status "Waiting for services to start..."
sleep 30

# Test endpoints
print_status "Testing MCP endpoints..."
if curl -f http://localhost:3001/health > /dev/null 2>&1; then
    print_success "✅ Web3 Research MCP Bridge is healthy"
else
    print_error "❌ Web3 Research MCP Bridge is not responding"
fi

if curl -f http://localhost:3002/health > /dev/null 2>&1; then
    print_success "✅ Whitepapers MCP Bridge is healthy"
else
    print_error "❌ Whitepapers MCP Bridge is not responding"
fi

# Final instructions
echo ""
print_success "🎉 MCP Deployment Complete!"
echo ""
print_status "Your MCP servers are now available at:"
print_status "• Web3 Research: https://$DOMAIN_NAME/web3"
print_status "• Whitepapers: https://$DOMAIN_NAME/whitepapers"
echo ""
print_status "Update your day-8-backend/.env file:"
echo "MCP_WEB3_URL=https://$DOMAIN_NAME/web3"
echo "MCP_WHITEPAPER_URL=https://$DOMAIN_NAME/whitepapers"
echo ""
print_status "Useful commands:"
print_status "• Check status: docker-compose ps"
print_status "• View logs: docker-compose logs -f"
print_status "• Restart: sudo systemctl restart mcp-deployment"
print_status "• Stop: sudo systemctl stop mcp-deployment"
echo ""
print_warning "⚠️  Make sure to configure your Cloudflare tunnel to route:"
print_warning "   $DOMAIN_NAME/web3/* -> http://web3-mcp-bridge:3001/"
print_warning "   $DOMAIN_NAME/whitepapers/* -> http://whitepapers-mcp-bridge:3002/"
echo ""
print_success "Deployment completed successfully! 🚀"
