# AICluster Installation Documentation

Welcome to AICluster v2.0.0. This documentation will guide you through installing, configuring, and operating AICluster.

## Quick Links

| Document | Description | Read This If... |
|----------|-------------|-----------------|
| [INSTALLATION.md](INSTALLATION.md) | Complete installation guide | You're installing AICluster for the first time |
| [QUICK_START.md](QUICK_START.md) | 5-minute setup | You want to get started immediately |
| [FIRST_CLUSTER.md](FIRST_CLUSTER.md) | Building a multi-machine cluster | You're setting up multiple workers |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment | You're deploying to production |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common problems and solutions | Something isn't working |
| [FAQ.md](FAQ.md) | Frequently asked questions | You have general questions |
| [UPGRADING.md](UPGRADING.md) | Upgrading from v2.0.0 | You're upgrading an existing installation |

## Installation Overview

```
                      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                      â”‚  Read INSTALLATION.md â”‚
                      â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                 â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚                         â”‚
                    â–¼                         â–¼
          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
          â”‚ First Time User  â”‚      â”‚  Existing User   â”‚
          â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜      â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                   â”‚                        â”‚
                   â–¼                        â–¼
          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
          â”‚  QUICK_START.md  â”‚      â”‚  UPGRADING.md   â”‚
          â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜      â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                   â”‚                        â”‚
                   â–¼                        â–¼
          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”      â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
          â”‚ FIRST_CLUSTER.md â”‚      â”‚  Verification   â”‚
          â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜      â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                   â”‚
                   â–¼
          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
          â”‚ DEPLOYMENT.md   â”‚
          â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Quick Start for the Impatient

```powershell
# 1. Install Python 3.12+
# 2. Clone the repo
git clone https://github.com/manojkumar12-maker/AICluster-Studio.git
cd AICluster-Studio

# 3. Install dependencies
pip install -r backend/requirements.txt
pip install slowapi pytest pytest-asyncio httpx

# 4. Start the master
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. Note the admin password printed to console
# 6. Open http://localhost:3000 in your browser
# 7. Log in with username "admin" and the printed password
```

## File Overview

| File | Description | ~Size |
|------|-------------|-------|
| `INSTALLATION.md` | Complete installation guide with all methods | 80 KB |
| `QUICK_START.md` | 5-minute quick start guide | 5 KB |
| `FIRST_CLUSTER.md` | Multi-machine cluster setup guide | 25 KB |
| `DEPLOYMENT.md` | Production hardening and operations | 50 KB |
| `TROUBLESHOOTING.md` | 45 common problems with solutions | 30 KB |
| `FAQ.md` | 55 frequently asked questions | 25 KB |
| `UPGRADING.md` | v2.0.0 to v2.0.0 upgrade guide | 20 KB |

## System Requirements Summary

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 22H2 | Windows 11 Pro |
| CPU | 4 cores (i5) | 8 cores (i7/Ultra 7) |
| RAM | 16 GB | 32-64 GB |
| Disk | 10 GB SSD | 50 GB NVMe |
| Python | 3.12 | 3.12 |
| Network | DHCP LAN | 1 Gbps static IP |

## Need Help?

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
2. Check [FAQ.md](FAQ.md) for general questions
3. Open a GitHub issue at [AICluster-Studio](https://github.com/manojkumar12-maker/AICluster-Studio/issues)
