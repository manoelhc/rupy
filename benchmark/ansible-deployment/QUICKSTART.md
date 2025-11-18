# Quick Setup Guide

## Prerequisites

1. **Control Machine** (your laptop/workstation):
   - Python 3.8+
   - Ansible 2.12+

2. **Three Ubuntu 24.04 Servers**:
   - SSH access configured
   - Python 3 installed
   - Sudo privileges

## Step 1: Install Ansible

On your control machine:

```bash
pip install -r requirements.txt
```

## Step 2: Configure SSH Access

Ensure SSH key-based authentication is set up:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096

# Copy SSH key to all servers
ssh-copy-id ubuntu@<locust-server-ip>
ssh-copy-id ubuntu@<app-server-ip>
ssh-copy-id ubuntu@<db-server-ip>

# Test SSH access
ssh ubuntu@<locust-server-ip>
```

## Step 3: Update Inventory

Edit `inventory.yml` and replace the IP addresses:

```yaml
locust-server:
  ansible_host: YOUR_LOCUST_SERVER_IP

app-server:
  ansible_host: YOUR_APP_SERVER_IP

db-server:
  ansible_host: YOUR_DB_SERVER_IP
```

## Step 4: Update Variables

Edit `group_vars/all.yml` and change:
- `db_password` - Database password
- `postgres_admin_password` - PostgreSQL admin password
- `allowed_ssh_ips` - Your IP address for SSH access

## Step 5: Test Connectivity

```bash
./deploy.sh check
```

This will:
- Verify Ansible is installed
- Check inventory configuration
- Test SSH connectivity to all servers

## Step 6: Deploy

```bash
./deploy.sh deploy
```

This will:
1. Install common packages on all servers
2. Set up PostgreSQL on database server
3. Deploy all 6 frameworks on app server
4. Set up Locust on locust server

Deployment takes about 10-15 minutes.

## Step 7: Verify Deployment

```bash
./deploy.sh status
```

Check that all services are running.

## Step 8: Access Services

```bash
./deploy.sh info
```

This shows:
- Locust Web UI URL
- All framework endpoints
- Database connection info

## Step 9: Run Load Tests

### Option 1: Use the Web UI

Open `http://<locust-server-ip>:8089` in your browser.

### Option 2: Use the CLI

SSH to the locust server:

```bash
ssh ubuntu@<locust-server-ip>
cd /opt/benchmark/locust
./run_test.sh rupy 100 10 60s
```

### Option 3: Manual Locust Command

```bash
ssh ubuntu@<locust-server-ip>
locust -f /opt/benchmark/locust/locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s \
  --host http://<app-server-ip>:8001 \
  --html report.html
```

## Troubleshooting

### SSH Connection Failed

```bash
# Check SSH connectivity
ansible all -m ping -vvv

# Try manual SSH
ssh -v ubuntu@<server-ip>
```

### Service Not Starting

```bash
# Check logs on app server
ssh ubuntu@<app-server-ip>
sudo journalctl -u app-rupy -n 50
```

### Database Connection Issues

```bash
# Test database from app server
ssh ubuntu@<app-server-ip>
psql -h <db-server-ip> -U benchmark -d benchmark
```

## Management Commands

```bash
# Start all services
./deploy.sh start

# Stop all services
./deploy.sh stop

# Restart all services
./deploy.sh restart

# Check status
./deploy.sh status

# Show deployment info
./deploy.sh info
```

## Re-deployment

To update the code or configuration:

```bash
# Re-run specific playbook
ansible-playbook -i inventory.yml playbooks/apps.yml

# Or full re-deployment
./deploy.sh deploy
```

## Security Recommendations

1. Change default passwords in `group_vars/all.yml`
2. Update `allowed_ssh_ips` to restrict SSH access
3. Use Ansible Vault for sensitive data:
   ```bash
   ansible-vault encrypt group_vars/all.yml
   ```
4. Configure UFW to restrict access between servers

## Performance Tuning

After deployment, you can adjust:
- `gunicorn_workers` in `group_vars/all.yml`
- PostgreSQL settings in `playbooks/database.yml`
- System limits in `playbooks/common.yml`

Then re-run:
```bash
ansible-playbook -i inventory.yml playbooks/apps.yml --tags config
```
