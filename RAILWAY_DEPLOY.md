# Railway Deployment Guide

## Quick Railway Deployment

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Login and Initialize
```bash
# Login to Railway
railway login

# Initialize project in this directory
railway init

# When prompted:
# - Project name: "mvp-iam-backend" (or your preferred name)
# - Template: Select "Empty Project"
```

### 3. Add PostgreSQL Database
```bash
# Add PostgreSQL service
railway add postgresql

# This automatically creates a database and sets DATABASE_URL
```

### 4. Set Environment Variables
```bash
# Set your demo token (or generate a secure one)
railway variables set DEMO_API_TOKEN=demo-token-12345

# Set allowed origins for your frontend
railway variables set ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173

# Set production mode
railway variables set DEBUG=false

# App name
railway variables set APP_NAME="MVP IAM Backend"
```

### 5. Deploy
```bash
# Deploy your backend
railway up

# Railway will:
# - Build your Python app
# - Run database migrations automatically  
# - Start the FastAPI server
# - Provide you with a public URL
```

### 6. Run Database Setup
After first deployment, you need to run migrations and seed data:

```bash
# Connect to your Railway project
railway shell

# Run migrations
alembic upgrade head

# Seed with sample data
python seed_db.py

# Exit
exit
```

## Your Backend is Live! 🚀

After deployment, you'll get:
- **API URL**: `https://your-project.railway.app`
- **Health Check**: `https://your-project.railway.app/health`
- **API Docs**: `https://your-project.railway.app/docs`

## Frontend Integration

Update your frontend environment variables:

```env
# Vercel Environment Variables
NEXT_PUBLIC_API_URL=https://your-project.railway.app
NEXT_PUBLIC_API_TOKEN=demo-token-12345
```

## Monitoring & Management

### Railway Dashboard
- **Deployments**: View build logs and deployment history
- **Metrics**: CPU, memory, and request metrics
- **Logs**: Real-time application logs
- **Variables**: Manage environment variables
- **Database**: PostgreSQL management interface

### Useful Railway Commands
```bash
# View logs
railway logs

# Open dashboard
railway open

# Connect to database
railway connect postgresql

# View current variables
railway variables

# Redeploy
railway up --detach
```

## Scaling & Pricing

**Railway Pricing** (as of 2024):
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage
- **Database**: ~$5-15/month depending on usage

**Automatic Scaling**:
- Railway auto-scales based on demand
- Handles traffic spikes automatically
- No manual intervention needed

## Production Checklist

✅ **Security**:
- [ ] Generate secure `DEMO_API_TOKEN` (not demo-token-12345)
- [ ] Set `ALLOWED_ORIGINS` to your actual frontend domain
- [ ] Set `DEBUG=false`

✅ **Database**:
- [ ] Migrations run successfully (`alembic upgrade head`)
- [ ] Sample data seeded (`python seed_db.py`)
- [ ] Database backups enabled in Railway dashboard

✅ **Monitoring**:
- [ ] Health check responding: `/health`
- [ ] API docs accessible: `/docs`
- [ ] Test key endpoints with authentication

✅ **Frontend**:
- [ ] Frontend deployed to Vercel
- [ ] Environment variables updated
- [ ] CORS working correctly

## Troubleshooting

**Build Issues**:
```bash
# Check build logs
railway logs --deployment

# Rebuild
railway up
```

**Database Connection Issues**:
```bash
# Check if DATABASE_URL is set
railway variables

# Test database connection
railway shell
python -c "from backend.app.db.session import engine; print('DB Connected!' if engine else 'Failed')"
```

**CORS Issues**:
```bash
# Update allowed origins
railway variables set ALLOWED_ORIGINS=https://your-domain.vercel.app,http://localhost:5173
```

Your MVP IAM platform is now production-ready on Railway! 🎉
