# Railway Deployment Checklist

## Pre-Deployment Verification

### Configuration Files
- [x] `railway.json` - Configured with proper health checks and start command
- [x] `nixpacks.toml` - Updated with correct dependencies and start command
- [x] `Dockerfile` - Production-ready with health checks and proper user setup
- [x] `requirements.txt` - All dependencies listed with versions
- [x] `Procfile` - Backup start command for Heroku-style deployment

### Application Health
- [x] Health check endpoint (`/health`) - Comprehensive with DB connectivity check
- [x] Readiness probe (`/readiness`) - Database connection validation
- [x] Liveness probe (`/liveness`) - Basic application health
- [x] Root endpoint (`/`) - API information

### Database Configuration
- [x] Alembic migrations configured for Railway
- [x] Database URL conversion (postgresql:// → postgresql+psycopg://)
- [x] Connection pooling optimized for production
- [x] Migration auto-run on startup

### Environment Variables
- [x] `DATABASE_URL` - Automatically provided by Railway PostgreSQL
- [x] `DEMO_API_TOKEN` - Set in deployment script
- [x] `ALLOWED_ORIGINS` - Production domains configured
- [x] `DEBUG=false` - Production setting
- [x] `RAILWAY_ENVIRONMENT=production` - Environment flag
- [x] `PORT` - Automatically provided by Railway

### Security & Production Readiness
- [x] Non-root user in Docker
- [x] CORS properly configured for production
- [x] Debug mode disabled in production
- [x] Connection pool settings optimized
- [x] Health check timeout increased for Railway

## Deployment Steps

1. **Install Railway CLI** (if not already installed):
   ```bash
   npm install -g @railway/cli
   ```

2. **Run the deployment script**:
   ```bash
   ./deploy_railway.sh
   ```

3. **Verify deployment**:
   - Check health endpoint: `https://your-app.railway.app/health`
   - Check API docs: `https://your-app.railway.app/docs`
   - Verify database migrations completed

## Manual Deployment Alternative

If the automated script fails, deploy manually:

```bash
# Login to Railway
railway login

# Initialize project
railway init

# Add PostgreSQL
railway add postgresql

# Set environment variables
railway variables set DEBUG="false"
railway variables set RAILWAY_ENVIRONMENT="production"
railway variables set ALLOWED_ORIGINS="https://your-frontend-domain.com"

# Deploy
railway up
```

## Post-Deployment Verification

### Health Checks
- [ ] `/health` returns healthy status with database check
- [ ] `/readiness` returns ready status
- [ ] `/liveness` returns alive status
- [ ] `/docs` loads FastAPI documentation

### Database
- [ ] Database migrations applied successfully
- [ ] Database connection working
- [ ] Sample data seeded (if SEED_DATABASE=true)

### API Endpoints
- [ ] All API routes accessible
- [ ] CORS working for frontend domains
- [ ] Authentication endpoints working

## Troubleshooting

### Common Issues

1. **Database connection fails**:
   - Check DATABASE_URL environment variable
   - Verify PostgreSQL service is added to Railway project

2. **Health check fails**:
   - Check application logs in Railway dashboard
   - Verify health check endpoint accessibility
   - Ensure health check timeout is sufficient

3. **Migration errors**:
   - Check Alembic configuration
   - Verify database permissions
   - Check migration file syntax

4. **CORS errors**:
   - Verify ALLOWED_ORIGINS environment variable
   - Check frontend domain configuration

### Monitoring
- Use Railway dashboard for logs and metrics
- Monitor health check status
- Set up alerts for service failures

## Success Indicators

**Deployment Successful When**:
- Health endpoint returns 200 OK
- Database migrations completed
- All API endpoints accessible
- No error logs in Railway dashboard
- Frontend can connect to API (CORS working)

## Rollback Plan

If deployment fails:
1. Check Railway logs for errors
2. Revert to previous deployment via Railway dashboard
3. Fix issues locally and redeploy
4. Consider using Railway's built-in rollback feature
