# Identity Management Platform MVP

> **The Bloomberg Terminal for Identity** - A vendor-neutral IAM tool that shows you independently what's going on in your environment.

## Quick Start

This is a comprehensive identity management platform that provides a single source of truth for all user identities, devices, and access permissions across your organization.

### Key Features
- **Canonical Identity System** - Single UUID that ties everything together
- **Vendor-Neutral** - Works with any identity provider (Okta, Azure AD, etc.)
- **Real-time Monitoring** - Live device and access tracking
- **Audit Insurance** - Immutable audit trails with cryptographic integrity
- **Compliance Ready** - Built-in compliance frameworks (SOX, PCI, GDPR, etc.)

## Documentation

**All documentation has been organized in the [`docs/`](docs/) folder.**

### Quick Links:
- **[Complete Documentation](docs/README.md)** - Full documentation index
- **[Frontend Guide](docs/frontend/FRONTEND_DEVELOPER_GUIDE.md)** - Frontend development
- **[API Reference](docs/api/API_ENDPOINTS_UPDATED.md)** - Complete API documentation
- **[Deployment Guide](docs/deployment/RAILWAY_DEPLOY.md)** - Railway deployment
- **[Technical Analysis](docs/analysis/)** - Deep technical guides

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React/Vue)   │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Identity Agent  │
                       │ (Windows Service)│
                       └─────────────────┘
```

## Tech Stack

- **Backend**: FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: React/Vue (your choice)
- **Deployment**: Railway
- **Authentication**: OAuth 2.0, JWT
- **Monitoring**: Built-in audit trails and compliance reporting

## Getting Started

1. **Read the Documentation**: Start with the [complete documentation](docs/README.md)
2. **Set up Backend**: Follow the [deployment guide](docs/deployment/RAILWAY_DEPLOY.md)
3. **Build Frontend**: Use the [frontend developer guide](docs/frontend/FRONTEND_DEVELOPER_GUIDE.md)
4. **Configure Integrations**: See the [API integration guides](docs/api/)

## Philosophy

> "We don't compete with Okta, Azure AD, or CrowdStrike - we make them better by showing you the truth across ALL your systems."

This platform is designed to be the **independent auditor** that enterprises can trust to provide an unbiased view of their identity landscape.

## Support

For questions or issues:
1. Check the [documentation](docs/README.md) first
2. Look at the [technical analysis](docs/analysis/) for deep dives
3. Review the [API reference](docs/api/API_ENDPOINTS_UPDATED.md) for implementation details

---

**Ready to get started?** Head to the [Complete Documentation](docs/README.md) to begin your journey with the Identity Management Platform.
