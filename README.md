# VakilJui – Legal Services Platform

Production-oriented Django platform designed for legal services, lawyer discovery, AI-powered legal assistance, and content management.

---

## Overview

VakilJui is a Django-based web platform developed with a focus on maintainability, modular architecture, and real-world deployment requirements. The platform integrates an AI-powered legal assistant that analyzes user queries, detects relevant legal specialties, and recommends appropriate lawyers.

The project demonstrates backend development practices for legal and service-oriented platforms, including content management, user workflows, SEO optimization, and scalable application structure.

---

## Project Goals

- Provide a structured legal services platform with lawyer discovery
- Deliver AI-powered legal query analysis and specialty detection
- Enable SEO-friendly content delivery through structured data and dynamic sitemaps
- Maintain clean and extensible backend architecture
- Support future API expansion and integrations
- Enable scalable growth through modular design

---

## Architecture

The system follows a modular Django architecture:

- Core project configuration
- Independent domain apps (accounts, home, lawyers, etc.)
- Reusable templates and components
- Service-oriented backend structure
- AI integration module for legal query processing

Designed with support for:

- Django REST Framework (DRF) ready
- Background task processing (Celery)
- Redis caching
- Docker-based deployment
- Nginx reverse proxy

---

## Tech Stack

- Python 3.11+
- Django 4.x
- Django Templates (server-side rendering)
- PostgreSQL (production) / SQLite (development)
- Linux (Ubuntu) deployment
- Gunicorn WSGI server
- Nginx reverse proxy
- Redis for caching and session storage
- Celery for background tasks
- Git for version control

---

## Key Features

### Core Platform
- User authentication (login, registration, logout)
- Lawyer profile management with detailed information
- Lawyer subscription plans (gold, premium)
- Lawyer listing with filtering by specialty and city
- Lawyer detail pages with SEO metadata
- Content management system for landing pages

### AI-Powered Legal Assistant
- Floating widget accessible site-wide
- Natural language query input
- Integration with Claude API for legal analysis
- Automatic specialty detection (family, property, criminal, etc.)
- City extraction from user description
- Lawyer recommendation based on detected specialties and location
- Rate limiting to prevent API abuse
- SEO-friendly public pages via query parameter (?q=...)
- JSON-LD structured data (FAQPage schema) for search engine visibility

### SEO & Content Delivery
- Dynamic sitemap generation including AI query pages
- Canonical URL management to avoid duplicate content
- Open Graph and Twitter Card meta tags
- Breadcrumb schema for lawyer listing and detail pages
- LocalBusiness schema for location-based legal services
- Attorney schema for lawyer profiles
- Internal linking via footer and related content sections

### Administration & Management
- Django admin interface for content management
- Specialty and city management
- Landing page content customization
- Lawyer subscription management

---

## Project Structure

```
vakiljui/
├── core/                    # Project settings and main URL configuration
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   └── urls.py
├── apps/                    # All application modules
│   ├── accounts/            # User authentication and profiles
│   ├── home/                # Main application with views, templates, AI integration
│   │   ├── views.py         # HomeView, LawyerListView, AIMatchView, etc.
│   │   ├── ai_matcher.py    # Claude API integration and query analysis
│   │   ├── sitemaps.py      # Sitemap definitions including AI queries
│   │   ├── models.py        # LawyerProfile, Specialty, City, Subscription, etc.
│   │   ├── urls.py          # URL routing for home app
│   │   └── templatetags/    # Custom template tags
│   └── lawyers/             # Additional lawyer management (if separate)
├── templates/               # Global HTML templates
│   ├── base.html            # Base template with navbar, hero, footer, AI widget
│   └── home/
│       ├── index.html       # Landing page
│       ├── lawyer_list.html
│       ├── lawyer_detail.html
│       └── seo_landing.html
├── static/                  # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   ├── fonts/
│   └── img/
├── media/                   # User-uploaded files (lawyer images, etc.)
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## AI Module Details

The AI module (`ai_matcher.py`) is responsible for:

1. Receiving a user description (natural language)
2. Sending the query to Anthropic Claude API with a structured prompt
3. Parsing the JSON response to extract:
   - Detected legal specialties (e.g., family, property, criminal)
   - Mentioned city (if any)
   - A concise summary of the legal situation
4. Returning structured data for further processing

The prompt engineering ensures Claude outputs valid JSON with predefined keys, making integration robust and error-resistant.

---

## SEO Optimization Strategy

### Dynamic Query Pages
- Pages with `?q=<query>` contain the full question and AI-generated answer in the HTML source
- Each query page is treated as a unique page by search engines
- Canonical URL points to the root to avoid duplicate content issues

### Structured Data (JSON-LD)
- `FAQPage` schema for AI Q&A content
- `Attorney` schema for lawyer profiles
- `LocalBusiness` schema for specialty+city landing pages
- `BreadcrumbList` for navigation paths
- `WebSite` schema for site-wide SEO

### Sitemap
- Multiple sitemap indexes: lawyer profiles, landing pages, lawyer lists, static pages, and AI query pages
- AI query sitemap includes a curated list of common legal questions

### Internal Linking
- Footer section with clickable links to popular AI queries
- Related lawyers section on detail pages
- Specialty and city navigation from the homepage

---

## Installation

### Clone repository

```bash
git clone https://github.com/abbas4007/vakiljui.git
cd vakiljui
```

### Create virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### Install requirements

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file based on `.env.example` with:
- Django secret key
- Database credentials
- Claude API key
- Redis URL (if using)
- Zarinpal merchant ID (for payments)

### Apply migrations

```bash
python manage.py migrate
```

### Collect static files

```bash
python manage.py collectstatic
```

### Run development server

```bash
python manage.py runserver
```

Access the application at:

```text
http://127.0.0.1:8000
```

---

## Docker Deployment

The project includes Docker and Docker Compose configuration for production-like deployment.

### Build and run containers

```bash
docker compose up -d --build
```

### Services
- `web`: Django application with Gunicorn
- `nginx`: Reverse proxy for static/media files
- `postgres`: PostgreSQL database
- `redis`: Redis cache and session store
- `celery`: Background task worker
- `celery_beat`: Scheduled task scheduler
- `certbot`: SSL certificate management

### Management commands inside container

```bash
docker compose exec web python manage.py <command>
```

### Clear cache

```bash
docker compose exec redis redis-cli FLUSHALL
```

### View logs

```bash
docker compose logs -f web
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ai_match/` | POST | Accepts user description and returns specialties, summary, and lawyer recommendations |
| `/جستجو` | GET | Search lawyers by keyword |
| `/sitemap.xml` | GET | Sitemap index |
| `/robots.txt` | GET | Robots directives |

---

## Testing

Run the test suite:

```bash
python manage.py test
```

---

## Maintenance

### Adding new legal specialties
1. Create a new `Specialty` object via admin or shell
2. Ensure `is_active=True`
3. Clear Redis cache: `docker compose exec redis redis-cli FLUSHALL`

### Adding new AI query sitemap entries
Edit the `queries` list in `home/sitemaps.py` under the `AiQuerySitemap.items()` method.

### Updating lawyer subscription plans
Manage through the Django admin interface under `SubscriptionPlan`.

---

## Author

Abbas Esmaeili

Python Backend Developer (Django / DRF)

Specialized in scalable backend systems, automation, and production web applications.

---

## License

This repository is shared for portfolio and evaluation purposes. All rights reserved.