# VPS Deployment Guide: MCP HTTP Bridges

## Overview

This guide provides comprehensive instructions for deploying MCP HTTP bridges on a VPS with Cloudflare Tunnel for HTTPS access. This deployment has been tested and proven to work on Ubuntu 24.04.

## Prerequisites

### VPS Requirements
- **OS**: Ubuntu 20.04+ (tested on 24.04)
- **RAM**: Minimum 2GB (4GB recommended)
- **CPU**: 2+ cores recommended
- **Storage**: Minimum 20GB SSD
- **Network**: Public IP address

### External Requirements
- **Domain Name**: Registered and managed through Cloudflare
- **Cloudflare Account**: With Zero Trust (free tier sufficient)
- **VPS Access**: SSH root access initially

## Pre-Deployment Setup

### 1. Cloudflare Configuration

#### Step 1: Domain Setup
1. Add your domain to Cloudflare (if not already added)
2. Set nameservers to Cloudflare's nameservers
3. Ensure DNS propagation is complete

#### Step 2: Create Cloudflare Tunnel
1. Login to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Select your domain
3. Navigate to **Zero Trust** → **Access** → **Tunnels**
4. Click **Create a tunnel**
5. Choose **Cloudflared** and click **Next**
6. Enter tunnel name (e.g., "mcp-tunnel") and click **Save tunnel**
7. Copy the tunnel token (starts with `eyJh...`) - you'll need this later
8. Configure tunnel routes:
   - **Subdomain**: `mcp`
   - **Domain**: `yourdomain.com`
   - **Path**: `web3`
   - **Service**: `http://nginx-proxy:80`
   - Click **Add rule**
   - **Subdomain**: `mcp`
   - **Domain**: `yourdomain.com`
   - **Path**: `whitepapers`
   - **Service**: `http://nginx-proxy:80`
9. Click **Save tunnel**

### 2. VPS Initial Setup

#### Connect to VPS
```bash
ssh root@your-vps-ip
```

#### Create Non-Root User
```bash
# Create user with sudo privileges
adduser mcp-user
usermod -aG sudo mcp-user

# Switch to new user
su - mcp-user
```

**IMPORTANT**: The deployment script MUST NOT be run as root. It includes checks to prevent this.

## Deployment Process

### 1. Download Deployment Files

```bash
# Create working directory
mkdir -p ~/vps-deployment
cd ~/vps-deployment

# Download deployment script (copy from your project)
# You'll need to copy the entire vps-deployment/ folder to the VPS
```

### 2. Make Script Executable

```bash
chmod +x deploy.sh
```

### 3. Run Deployment Script

```bash
./deploy.sh
```

The script will prompt you for:
- **Domain name** (e.g., `mcp.yourdomain.com`)
- **Cloudflare Tunnel Token** (from step 1.2.7 above)

### 4. Deployment Process

The script will automatically:

1. **Update system packages**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Docker**
   - Downloads and runs Docker installation script
   - Adds user to docker group
   - Installs Docker Compose

3. **Install Node.js 18.x**
   - Adds NodeSource repository
   - Installs Node.js and npm

4. **Setup Python environment**
   - Python 3.11 should be pre-installed on Ubuntu 24.04

5. **Clone MCP repositories**
   - `web3-research-mcp` from GitHub
   - `crypto-whitepapers-mcp` from GitHub

6. **Create HTTP bridges**
   - Node.js bridge for web3-research-mcp
   - Python Flask bridge for crypto-whitepapers-mcp

7. **Setup Docker environment**
   - Create docker-compose.yml
   - Configure nginx proxy
   - Setup Cloudflare tunnel container

8. **Build and start services**
   - Build Docker images
   - Start all containers
   - Configure health checks

## Post-Deployment Verification

### 1. Check Container Status

```bash
cd ~/vps-deployment
docker-compose ps
```

Expected output:
```
NAME                     IMAGE                                   COMMAND                  SERVICE                  CREATED             STATUS                     PORTS
cloudflared-tunnel       cloudflare/cloudflared:latest           "cloudflared --no-au…"   cloudflared              X minutes ago       Up X minutes               
nginx-proxy              nginx:alpine                            "/docker-entrypoint.…"   nginx-proxy              X minutes ago       Up X minutes               0.0.0.0:80->80/tcp
web3-mcp-bridge          vps-deployment-web3-mcp-bridge          "docker-entrypoint.s…"   web3-mcp-bridge          X minutes ago       Up X minutes (healthy)     0.0.0.0:3001->3001/tcp
whitepapers-mcp-bridge   vps-deployment-whitepapers-mcp-bridge   "python server.py"       whitepapers-mcp-bridge   X minutes ago       Up X minutes (healthy)     0.0.0.0:3002->3002/tcp
```

### 2. Test Local Endpoints

```bash
# Test health checks
curl http://localhost:3001/health
curl http://localhost:3002/health

# Test MCP tools
curl -X POST http://localhost:3001/tools/list -H "Content-Type: application/json" -d '{}'
```

### 3. Test External HTTPS Access

```bash
# Test via Cloudflare Tunnel
curl https://mcp.yourdomain.com/web3/health
curl https://mcp.yourdomain.com/whitepapers/health

# Test MCP tools via HTTPS
curl -X POST https://mcp.yourdomain.com/web3/tools/list -H "Content-Type: application/json" -d '{}'
```

## Troubleshooting

### Common Issues & Solutions

#### 1. Permission Errors
**Issue**: `permission denied while trying to connect to the Docker daemon socket`
**Solution**:
```bash
sudo usermod -aG docker $USER
newgrp docker
# Or logout and login again
```

#### 2. Container Build Failures
**Issue**: Missing Dockerfile or dependencies
**Solution**:
```bash
# Check if directories exist
ls -la web3-bridge/
ls -la whitepapers-bridge/

# Recreate missing files if needed
```

#### 3. Network Issues
**Issue**: Containers can't communicate
**Solution**:
```bash
# Check Docker network
docker network inspect mcp-network

# Test container connectivity
docker exec nginx-proxy ping web3-mcp-bridge
```

#### 4. Cloudflare Tunnel Issues
**Issue**: 502 errors or tunnel not connecting
**Solution**:
```bash
# Check tunnel logs
docker logs cloudflared-tunnel

# Verify tunnel token is correct
# Check Cloudflare dashboard for tunnel status
```

### Diagnostic Commands

```bash
# View all container logs
docker-compose logs

# View specific container logs
docker logs web3-mcp-bridge --tail 50
docker logs whitepapers-mcp-bridge --tail 50
docker logs nginx-proxy --tail 20
docker logs cloudflared-tunnel --tail 10

# Check container health
docker-compose ps
docker inspect web3-mcp-bridge | grep Health -A 10

# Test network connectivity
docker exec nginx-proxy nslookup web3-mcp-bridge
docker exec nginx-proxy ping web3-mcp-bridge

# Check port bindings
sudo netstat -tulpn | grep :3001
sudo netstat -tulpn | grep :3002
sudo netstat -tulpn | grep :80
```

## Maintenance

### Regular Maintenance Tasks

#### 1. Update Dependencies
```bash
cd ~/vps-deployment

# Pull latest MCP updates
cd web3-research-mcp && git pull && cd ..
cd crypto-whitepapers-mcp && git pull && cd ..

# Rebuild containers
docker-compose build
docker-compose up -d
```

#### 2. Monitor Resource Usage
```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check Docker resource usage
docker stats --no-stream
```

#### 3. Log Management
```bash
# Clean old Docker logs
docker system prune -f

# Check log sizes
sudo du -sh /var/lib/docker/containers/*/
```

### Backup & Recovery

#### 1. Backup Configuration
```bash
# Backup deployment directory
tar -czf mcp-deployment-backup-$(date +%Y%m%d).tar.gz ~/vps-deployment

# Store Cloudflare tunnel token securely
echo "TUNNEL_TOKEN=your-token-here" > ~/.env.backup
```

#### 2. Disaster Recovery
```bash
# Fresh deployment on new VPS
# 1. Copy backup to new VPS
# 2. Extract backup
tar -xzf mcp-deployment-backup-*.tar.gz

# 3. Run deployment script
cd vps-deployment
./deploy.sh
```

## Security Considerations

### 1. Firewall Configuration
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS (for tunnel)
sudo ufw allow 80
sudo ufw allow 443

# MCP ports (optional, as they're accessed via tunnel)
sudo ufw allow 3001
sudo ufw allow 3002
```

### 2. Regular Updates
```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Docker updates
sudo apt update && sudo apt install docker-ce docker-ce-cli containerd.io
```

### 3. Access Control
- Keep Cloudflare tunnel token secure
- Use strong SSH keys
- Regularly rotate access credentials
- Monitor access logs

## Performance Optimization

### 1. Docker Resource Limits
Edit `docker-compose.yml` to add resource limits:
```yaml
services:
  web3-mcp-bridge:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

### 2. Nginx Tuning
Optimize nginx configuration for production:
```nginx
events {
    worker_connections 2048;
}

http {
    # Enable gzip compression
    gzip on;
    gzip_types text/plain application/json;
    
    # Add caching headers
    expires 1h;
}
```

## Costs & Scaling

### Current Resource Usage
- **VPS**: ~$10-20/month (2GB RAM, 2 CPU)
- **Cloudflare**: Free tier sufficient
- **Bandwidth**: Minimal (API calls only)

### Scaling Considerations
- **Horizontal**: Multiple VPS instances with load balancer
- **Vertical**: Increase VPS resources
- **Regional**: Deploy in multiple regions for redundancy

## Support & Monitoring

### Health Monitoring
```bash
# Create monitoring script
cat > ~/monitor-mcp.sh << 'EOF'
#!/bin/bash
curl -f https://mcp.yourdomain.com/web3/health || echo "web3 DOWN"
curl -f https://mcp.yourdomain.com/whitepapers/health || echo "whitepapers DOWN"
EOF

chmod +x ~/monitor-mcp.sh

# Add to crontab for regular checks
echo "*/5 * * * * ~/monitor-mcp.sh" | crontab -
```

### Log Analysis
```bash
# Check for errors
docker-compose logs | grep -i error

# Monitor request patterns
docker logs nginx-proxy | grep "POST /web3"
docker logs nginx-proxy | grep "POST /whitepapers"
```

This guide provides a comprehensive, tested approach to deploying MCP HTTP bridges on a VPS. All steps have been validated and should result in a fully functional deployment.
