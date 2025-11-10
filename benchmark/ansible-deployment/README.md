# Ansible Deployment for Benchmark Load Tests

This Ansible project deploys the benchmark infrastructure across 3 separate Ubuntu 24.04 machines:

1. **Locust Server** - Load testing tool
2. **Application Server** - All 6 web framework APIs
3. **Database Server** - PostgreSQL database

## Prerequisites

- 3 Ubuntu 24.04 machines with SSH access
- Ansible installed on your control machine: `pip install ansible`
- Python 3.8+ on all target machines
- SSH key-based authentication configured

## Quick Start

### 1. Configure Your Inventory

Edit `inventory.yml` and update with your machine IPs/hostnames:

```yaml
all:
  children:
    locust:
      hosts:
        locust-server:
          ansible_host: 192.168.1.10
    apps:
      hosts:
        app-server:
          ansible_host: 192.168.1.11
    database:
      hosts:
        db-server:
          ansible_host: 192.168.1.12
```

### 2. Configure Variables

Edit `group_vars/all.yml` to customize your deployment:
- Database credentials
- Application ports
- Framework versions
- etc.

### 3. Deploy Everything

```bash
# Deploy all components
ansible-playbook -i inventory.yml site.yml

# Or deploy individually
ansible-playbook -i inventory.yml playbooks/database.yml
ansible-playbook -i inventory.yml playbooks/apps.yml
ansible-playbook -i inventory.yml playbooks/locust.yml
```

### 4. Run Load Tests

```bash
# SSH to locust server
ssh user@locust-server

# Run tests against any framework
locust -f /opt/benchmark/locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 60s \
  --host http://<app-server-ip>:8001 \
  --html report.html
```

Or access the Locust web UI at `http://<locust-server-ip>:8089`

## Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Locust Server  │─────>│  App Server     │─────>│  DB Server      │
│  Port 8089      │      │  Ports 8001-8006│      │  Port 5432      │
│                 │      │                 │      │                 │
│  - Locust Web UI│      │  - Rupy (8001)  │      │  - PostgreSQL   │
│  - Test Scripts │      │  - FastAPI(8002)│      │  - benchmark DB │
└─────────────────┘      │  - Django (8003)│      └─────────────────┘
                         │  - Flask  (8004)│
                         │  - Robyn  (8005)│
                         │  - mrhttp (8006)│
                         └─────────────────┘
```

## Playbooks

- `site.yml` - Main playbook that orchestrates all deployments
- `playbooks/database.yml` - Deploys PostgreSQL
- `playbooks/apps.yml` - Deploys all 6 web frameworks
- `playbooks/locust.yml` - Deploys Locust load testing tool
- `playbooks/common.yml` - Common setup for all servers

## Roles

- `roles/common` - Common packages and configuration
- `roles/postgresql` - PostgreSQL installation and configuration
- `roles/app-rupy` - Rupy framework deployment
- `roles/app-fastapi` - FastAPI framework deployment
- `roles/app-django` - Django REST framework deployment
- `roles/app-flask` - Flask-RESTful framework deployment
- `roles/app-robyn` - Robyn framework deployment
- `roles/app-mrhttp` - mrhttp framework deployment
- `roles/locust` - Locust installation and configuration

## Management Commands

```bash
# Start all services
ansible-playbook -i inventory.yml playbooks/manage.yml -e "action=start"

# Stop all services
ansible-playbook -i inventory.yml playbooks/manage.yml -e "action=stop"

# Restart all services
ansible-playbook -i inventory.yml playbooks/manage.yml -e "action=restart"

# Check status
ansible-playbook -i inventory.yml playbooks/manage.yml -e "action=status"
```

## Testing

```bash
# Verify connectivity
ansible all -i inventory.yml -m ping

# Check service status
ansible apps -i inventory.yml -a "systemctl status app-*"
ansible database -i inventory.yml -a "systemctl status postgresql"
ansible locust -i inventory.yml -a "systemctl status locust"
```

## Firewall Configuration

The playbooks automatically configure UFW firewall rules:
- Database server: Allow PostgreSQL (5432) from app server
- App server: Allow HTTP (8001-8006) from locust server
- Locust server: Allow web UI (8089) from your IP

## Customization

### Adding New Frameworks

1. Create a new role in `roles/app-newframework/`
2. Add the role to `playbooks/apps.yml`
3. Update `group_vars/all.yml` with framework configuration
4. Run the deployment

### Changing Ports

Edit `group_vars/all.yml` and update the port mappings, then re-run:
```bash
ansible-playbook -i inventory.yml playbooks/apps.yml --tags config
```

## Troubleshooting

### Connection Issues

```bash
# Test SSH connectivity
ansible all -i inventory.yml -m ping -vvv

# Check if Python is installed
ansible all -i inventory.yml -m raw -a "python3 --version"
```

### Service Issues

```bash
# Check logs
ansible apps -i inventory.yml -a "journalctl -u app-rupy -n 50"

# Restart services
ansible-playbook -i inventory.yml playbooks/manage.yml -e "action=restart"
```

### Database Connection Issues

```bash
# Test from app server
ansible apps -i inventory.yml -a "psql -h <db-ip> -U benchmark -d benchmark -c 'SELECT 1'"
```

## Security Considerations

- Use SSH key authentication (passwords disabled by default)
- Configure firewall rules appropriately
- Use strong database passwords
- Consider using Ansible Vault for sensitive data
- Keep systems updated with security patches

## Backup and Recovery

```bash
# Backup database
ansible database -i inventory.yml -a "pg_dump -U postgres benchmark > /backup/benchmark.sql"

# Restore database
ansible database -i inventory.yml -a "psql -U postgres benchmark < /backup/benchmark.sql"
```

## Performance Tuning

The playbooks include optimized configurations for:
- PostgreSQL connection pooling
- Application worker processes
- System resource limits
- Network buffer sizes

Adjust in `group_vars/all.yml` based on your machine specs.

## License

Same as the parent Rupy project (MIT).
