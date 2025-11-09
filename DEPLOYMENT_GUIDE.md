# Deployment Guide

## Database Isolation (Important!)

**Your database is already isolated!** Each deployment creates its own database with its own characters and memories.

### How It Works

When you share this code:

1. **Your Local Data Stays Local**
   - Characters, conversations, and memories are stored in Docker volumes
   - Docker volumes are stored in Docker's internal storage (not in the code repo)
   - `.gitignore` prevents accidental database file commits

2. **Each Deployment Gets Fresh Database**
   - When someone clones the repo and runs `docker-compose up`
   - They get a brand new, empty database
   - Their characters and data are completely separate from yours

3. **Data Locations**
   ```
   Your machine:
   - postgres_data (Docker volume) → Your characters & memories
   - redis_data (Docker volume) → Your cache
   - audio_cache/ (local folder) → Your generated audio files

   Their machine:
   - postgres_data (Docker volume) → Their characters & memories
   - redis_data (Docker volume) → Their cache
   - audio_cache/ (local folder) → Their generated audio files
   ```

### What Gets Shared vs What Stays Local

**✅ Shared (in Git repository):**
- Source code (`app/`, `static/`)
- Configuration templates (`.env.example`)
- Database schema (`init-db.sql`)
- Documentation (all `.md` files)
- Docker configuration (`docker-compose.yml`, `Dockerfile`)

**🔒 Stays Local (NOT in Git):**
- Database contents (characters, conversations, memories)
- Redis cache
- Generated audio files
- Your `.env` file with API keys
- Docker volumes

---

## Deployment Options

### Option 1: Local Development (Default)

This is what you're currently using - perfect for development!

```bash
# Clone the repo
git clone <your-repo-url>
cd RPGAI

# Copy environment file
cp .env.example .env

# Edit .env with your settings (optional)
nano .env

# Start services
docker-compose up -d

# Access at http://localhost:4020
```

**Data Location**: Docker volumes on your local machine

---

### Option 2: Share with Others (Clean Setup)

When others clone your repo, they automatically get a fresh database:

```bash
# They clone your repo
git clone <your-repo-url>
cd RPGAI

# They start services
docker-compose up -d

# They get their own database at http://localhost:4020
```

**Result**: Completely isolated - they can't see your characters!

---

### Option 3: Deploy to Production Server

For deploying to a VPS, cloud server, or dedicated machine:

#### Step 1: Prepare Server

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repo
git clone <your-repo-url>
cd RPGAI
```

#### Step 2: Configure Environment

```bash
# Copy and edit environment
cp .env.example .env
nano .env

# Important settings for production:
# - Set DEBUG=false
# - Change POSTGRES_PASSWORD to a strong password
# - Set your Ollama URL or OpenRouter API key
# - Consider changing default ports if needed
```

#### Step 3: Start Services

```bash
# Start in production mode
docker-compose up -d

# Check logs
docker-compose logs -f

# Access at http://your-server-ip:4020
```

#### Step 4: (Optional) Add Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/rpgai
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:4020;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then enable SSL with Let's Encrypt:
```bash
sudo certbot --nginx -d your-domain.com
```

---

## Data Persistence & Backup

### Viewing Your Docker Volumes

```bash
# List all volumes
docker volume ls

# Inspect postgres volume
docker volume inspect rpgai_postgres_data

# Location (typically):
# Mac: ~/Library/Containers/com.docker.docker/Data/vms/0/
# Linux: /var/lib/docker/volumes/
# Windows: \\wsl$\docker-desktop-data\data\docker\volumes\
```

### Backup Your Database

```bash
# Backup database
docker exec rpgai-postgres pg_dump -U rpgai rpgai > backup.sql

# Restore database
docker exec -i rpgai-postgres psql -U rpgai rpgai < backup.sql
```

### Reset Database (Start Fresh)

```bash
# WARNING: This deletes ALL characters and conversations!

# Stop services
docker-compose down

# Remove database volume
docker volume rm rpgai_postgres_data rpgai_redis_data

# Start fresh
docker-compose up -d
```

---

## Multi-User Setup (Single Server, Isolated Users)

If you want to run ONE server where multiple users have separate data:

### Current Design
- Uses `X-User-ID` header to separate user data
- Each user gets their own characters and conversations
- Characters remember individual users separately

### Usage
```bash
# User 1
curl -X POST http://localhost:4020/api/characters \
  -H "X-User-ID: alice" \
  -d '{"prompt": "A wizard"}'

# User 2
curl -X POST http://localhost:4020/api/characters \
  -H "X-User-ID: bob" \
  -d '{"prompt": "A warrior"}'

# Alice and Bob see different characters!
```

### For Production Multi-User
You may want to add authentication:

1. **JWT Authentication** (recommended for production)
2. **API Keys** (simple, good for game integration)
3. **OAuth** (if integrating with existing auth system)

See: [API_REFERENCE.md](API_REFERENCE.md) for current authentication setup.

---

## Environment Variables Reference

Key variables to set in `.env`:

### LLM Provider
```bash
# Option 1: Ollama (local, free)
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.1

# Option 2: OpenRouter (cloud)
DEFAULT_LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

### Database (change for production!)
```bash
DATABASE_URL=postgresql+asyncpg://rpgai:CHANGE_THIS_PASSWORD@postgres:5432/rpgai
DATABASE_PASSWORD=CHANGE_THIS_PASSWORD
```

### Voice Services
```bash
TTS_ENABLED=true
STT_ENABLED=true
WHISPER_MODEL=base-int8  # or: tiny, small, medium, large-v3
```

### Memory System
```bash
MEM0_ENABLE_MEMORY=true
MEM0_MODEL=granite4:micro  # Use small model for memory extraction
```

---

## Monitoring & Maintenance

### Check Service Health

```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs backend
docker-compose logs postgres
docker-compose logs whisper

# Check backend health
curl http://localhost:4020/health
```

### Resource Usage

```bash
# Check Docker resource usage
docker stats

# Check volume sizes
docker system df -v
```

### Updates

```bash
# Pull latest code
git pull

# Rebuild containers
docker-compose build

# Restart services
docker-compose up -d
```

---

## Troubleshooting

### "Port already in use"

```bash
# Change ports in docker-compose.yml
ports:
  - "4021:8000"  # Change 4020 to 4021
```

### "Database connection failed"

```bash
# Check postgres is healthy
docker-compose ps postgres

# View postgres logs
docker-compose logs postgres

# Restart postgres
docker-compose restart postgres
```

### "Ollama connection failed"

```bash
# Check Ollama is running on host
curl http://localhost:11434/api/tags

# Or use OpenRouter instead (edit .env)
DEFAULT_LLM_PROVIDER=openrouter
```

---

## Security Best Practices

### For Production Deployments

1. **Change Default Passwords**
   ```bash
   # In docker-compose.yml and .env
   POSTGRES_PASSWORD=use-a-strong-password-here
   ```

2. **Disable Debug Mode**
   ```bash
   DEBUG=false
   ```

3. **Add Firewall Rules**
   ```bash
   # Only expose port 4020 (or your chosen port)
   sudo ufw allow 4020/tcp
   sudo ufw enable
   ```

4. **Use HTTPS**
   - Add Nginx reverse proxy
   - Get SSL certificate with Let's Encrypt

5. **Secure API Access**
   - Implement JWT authentication
   - Use API rate limiting
   - Add API keys for game clients

6. **Regular Backups**
   ```bash
   # Add to crontab
   0 2 * * * docker exec rpgai-postgres pg_dump -U rpgai rpgai > /backups/rpgai-$(date +\%Y\%m\%d).sql
   ```

---

## Need Help?

- **Documentation**: See [README.md](README.md)
- **API Reference**: See [API_REFERENCE.md](API_REFERENCE.md)
- **Unreal Integration**: See [UNREAL_INTEGRATION.md](UNREAL_INTEGRATION.md)
- **Issues**: Check GitHub issues or create a new one

## Summary

**TL;DR**: Your database is already isolated! When you push your code to GitHub and others clone it:
- ✅ They get the code
- ✅ They get a fresh, empty database
- ✅ Your characters and data stay on your machine
- ✅ No configuration needed - it works automatically!
