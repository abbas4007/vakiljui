<h1 align="center">⚖️ VakilJui</h1>

<p align="center">
  <strong>Legal Services & Lawyer Discovery Platform</strong>
</p>

<p align="center">
  A production-oriented Django platform for lawyer discovery, legal services,
  content management, online consultation, and AI-powered assistance.
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge)
![Linux](https://img.shields.io/badge/Linux-Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)

</p>

---

## 📌 Overview

**VakilJui** is a production-oriented Django platform built for legal
services, lawyer discovery, content management, online consultation,
subscription management, and AI-assisted interactions.

The platform was developed around real-world business requirements,
with a focus on maintainability, modular architecture, automation,
scalability, and production deployment.

Unlike a simple demonstration project, VakilJui includes real application
workflows such as lawyer profiles, user management, subscriptions,
online consultations, background task processing, and integration with
an external AI model.

---

## 🎯 Project Goals

VakilJui aims to provide a structured digital platform for legal services
by connecting users with lawyers and providing tools for:

- ⚖️ Lawyer discovery
- 👤 User and profile management
- 💬 Online legal consultation
- 🤖 AI-powered consultation assistance
- 💳 Subscription management
- 📰 Content publishing and management
- 🔐 Platform administration
- ⚙️ Automated background processing

---

# ✨ Features

## ⚖️ Lawyer Discovery

- Lawyer profile management
- Professional information
- Legal specialty categorization
- Structured lawyer discovery
- SEO-friendly lawyer pages

---

## 👤 Authentication & User Management

- User registration
- User authentication
- User profiles
- Permission management
- Role-based workflows
- Account management

---

## 💬 Online Consultation

VakilJui includes a text-based online consultation system designed to
connect users with lawyers.

The consultation workflow supports:

- Consultation requests
- Text-based communication
- Lawyer responses
- Time-limited consultation sessions
- Consultation history
- User satisfaction / rating workflow

The consultation system is integrated directly into the platform's
business logic rather than being a standalone messaging component.

---

## 🤖 AI-Powered Consultation Assistant

VakilJui also includes an AI-powered consultation assistant.

The application connects to an external AI model and provides users
with an intelligent conversational interface.

### AI Workflow

```text
User Question
      │
      ▼
VakilJui
      │
      ▼
AI Consultation Service
      │
      ▼
External AI Model
      │
      ▼
Generated Response
      │
      ▼
User
```

The AI integration is implemented as part of the platform's consultation
workflow and is designed to keep the AI service separated from the core
business logic.

This makes it possible to change or extend the underlying AI model
without redesigning the entire application.

> AI-generated responses are intended for informational assistance and
> should not be considered a substitute for professional legal advice.

---

## 💳 Subscription Management

VakilJui includes a subscription management system for platform services.

The system manages the subscription lifecycle and automatically handles
expired subscriptions.

### Subscription Lifecycle

```text
Active Subscription
        │
        ▼
Expiration Date Reached
        │
        ▼
Scheduled Background Task
        │
        ▼
Check Subscription
        │
        ▼
Mark as Expired
```

Subscriptions are automatically marked as **expired** after their
validity period ends without requiring manual administrative action.

---

## ⏱️ Background Task Processing

VakilJui uses **Celery** and **Redis** for background and scheduled
processing.

One of the implemented workflows is automatic subscription expiration.

Celery periodically checks active subscriptions and updates their status
when their validity period has ended.

### Background Processing Flow

```text
                 Celery Beat
                     │
                     ▼
              Scheduled Task
                     │
                     ▼
          Check Active Subscriptions
                     │
                     ▼
             Expiration Reached?
                  /       \
                Yes        No
                 │          │
                 ▼          ▼
              Expired     Continue
```

This keeps scheduled business operations independent from the main
HTTP request/response cycle.

---

## 🔴 Redis

**Redis** is integrated into VakilJui as an in-memory data store and
is part of the background-processing infrastructure.

Redis works alongside Celery to support asynchronous and scheduled
application tasks.

```text
              Django
             /      \
            ▼        ▼
      PostgreSQL    Redis
                     │
                     ▼
                   Celery
                     │
                     ▼
              Background Tasks
```

---

## 📰 Content Management

VakilJui provides a dynamic content management system for managing
platform content.

Features include:

- Article management
- Dynamic content
- SEO-friendly URLs
- Metadata management
- Django Admin integration

---

## 🔐 Administration

The platform uses Django Admin for centralized administration of:

- Users
- Lawyers
- Content
- Subscriptions
- Consultation data
- Platform configuration

---

# 🏗️ Architecture

VakilJui follows a modular Django architecture with separate application
domains and production-oriented infrastructure.

```text
                         ┌──────────────────┐
                         │      Client      │
                         │ Browser / User   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │      Nginx       │
                         │  Reverse Proxy   │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     Gunicorn     │
                         │   WSGI Server    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │      Django      │
                         │   Application    │
                         └───────┬───┬──────┘
                                 │   │
                    ┌────────────┘   └─────────────┐
                    ▼                              ▼
           ┌─────────────────┐             ┌──────────────┐
           │   PostgreSQL    │             │    Redis     │
           │    Database     │             │ In-Memory DB │
           └─────────────────┘             └──────┬───────┘
                                                  │
                                                  ▼
                                           ┌──────────────┐
                                           │    Celery    │
                                           │ Background   │
                                           │    Tasks     │
                                           └──────────────┘
```

---

# 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | Django |
| Frontend | Django Templates |
| Database | PostgreSQL |
| In-Memory Data Store | Redis |
| Background Tasks | Celery |
| Web Server | Nginx |
| Application Server | Gunicorn |
| Operating System | Linux / Ubuntu |
| Version Control | Git |
| CI/CD | GitHub Actions |
| AI Integration | External AI Model |

---

# 📂 Project Structure

```text
vakiljui/
│
├── .github/
│   └── workflows/
│
├── core/
│
├── apps/
│
├── templates/
│
├── static/
│
├── media/
│
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

The application is organized around independent Django modules to keep
business domains separated and maintainable.

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/abbas4007/vakiljui.git
cd vakiljui
```

## 2. Create a virtual environment

### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Configure the required environment variables for your local environment.

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DATABASE_NAME=your-database
DATABASE_USER=your-user
DATABASE_PASSWORD=your-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

REDIS_URL=redis://localhost:6379/0

AI_API_KEY=your-api-key
```

> Never commit production secrets, API keys, passwords, or private
> credentials to the repository.

## 5. Apply migrations

```bash
python manage.py migrate
```

## 6. Create an administrator

```bash
python manage.py createsuperuser
```

## 7. Run the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000
```

---

# 🚀 Running Background Tasks

If Redis and Celery are configured locally, start the Celery worker:

```bash
celery -A core worker -l info
```

If Celery Beat is used for scheduled tasks:

```bash
celery -A core beat -l info
```

> Adjust the Celery application path if your project uses a different
> Celery configuration.

---

# 🚢 Production Deployment

VakilJui has been designed with real-world deployment requirements
in mind.

A typical production architecture consists of:

```text
Internet
   │
   ▼
 Nginx
   │
   ▼
Gunicorn
   │
   ▼
Django
 ┌─┴──────────────┐
 ▼                ▼
PostgreSQL       Redis
                    │
                    ▼
                 Celery
```

Production infrastructure includes:

- Ubuntu Linux
- Nginx
- Gunicorn
- PostgreSQL
- Redis
- Celery
- HTTPS / SSL
- Environment-based configuration
- Static and media file handling

---

# 🔄 CI/CD

The repository includes GitHub Actions workflows under:

```text
.github/workflows/
```

These workflows provide a foundation for automated project checks and
future continuous integration and deployment improvements.

---

# 🧪 Testing

The project supports Django's testing framework for validating application
logic and critical workflows.

Run tests with:

```bash
python manage.py test
```

---

# 🔒 Security

Security is considered throughout the application and deployment process.

Before deploying to production:

- Set `DEBUG=False`
- Use a strong `SECRET_KEY`
- Configure allowed hosts
- Use HTTPS
- Keep credentials outside the repository
- Protect database credentials
- Configure secure cookies
- Keep dependencies updated
- Never expose AI API keys

If you discover a security issue, please avoid publishing sensitive
details publicly before it has been reviewed.

---

# 🗺️ Roadmap

### Completed

- [x] Django application foundation
- [x] User authentication
- [x] Lawyer profiles
- [x] Lawyer discovery
- [x] Content management
- [x] Subscription management
- [x] Automatic subscription expiration
- [x] Online text consultation
- [x] AI-powered consultation assistant
- [x] External AI model integration
- [x] Redis integration
- [x] Celery background processing
- [x] Scheduled background tasks
- [x] PostgreSQL
- [x] Nginx + Gunicorn
- [x] Linux deployment
- [x] GitHub Actions workflow

### Planned

- [ ] Django REST Framework API
- [ ] Dockerized deployment
- [ ] Advanced search
- [ ] Improved AI context management
- [ ] AI conversation history optimization
- [ ] Notification system
- [ ] Performance optimization
- [ ] Expanded automated test coverage

---

# 📸 Screenshots

Screenshots and product demonstrations will be added here.

Recommended structure:

```text
docs/
├── banner.png
├── home.png
├── lawyers.png
├── consultation.png
├── ai-consultation.png
├── admin.png
└── demo.gif
```

---

# 🎥 Demo

A product demonstration showing the main VakilJui workflows will be
added here.

Planned demonstration:

```text
User Registration
       │
       ▼
Lawyer Discovery
       │
       ▼
Lawyer Profile
       │
       ▼
Online Consultation
       │
       ▼
AI Consultation
       │
       ▼
Subscription Management
```

---

# 🧠 Engineering Focus

VakilJui demonstrates practical experience with:

- Django backend development
- Modular application architecture
- Database-driven applications
- Authentication and authorization
- Lawyer discovery systems
- Subscription lifecycle management
- Online consultation workflows
- AI model integration
- Background task processing
- Celery
- Redis
- PostgreSQL
- Nginx
- Gunicorn
- Linux server deployment
- SEO-oriented architecture
- GitHub Actions
- Production-oriented development practices

---

# 🔮 Future Architecture

As the platform grows, additional infrastructure can be introduced
without changing the core business architecture.

```text
                         Client
                           │
                           ▼
                         Nginx
                           │
                           ▼
                        Django
                    ┌──────┼──────┐
                    │      │      │
                    ▼      ▼      ▼
              PostgreSQL  Redis   AI Service
                            │
                            ▼
                          Celery
                            │
                            ▼
                    Background Tasks
```

Potential future improvements include:

- REST API with Django REST Framework
- Containerized deployment with Docker
- Advanced caching strategies
- Distributed background processing
- Advanced search infrastructure
- Expanded AI capabilities

---

# 🤝 Contributing

VakilJui is primarily maintained as a portfolio and production-oriented
project.

If you would like to contribute:

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/your-feature
```

3. Make your changes
4. Run tests

```bash
python manage.py test
```

5. Commit your changes

```bash
git commit -m "Add: your feature"
```

6. Push your branch

```bash
git push origin feature/your-feature
```

7. Open a Pull Request

---

# 👨‍💻 Author

## Abbas Esmaili

**Python / Django Backend Developer**

Focused on:

- Backend Development
- Django
- Scalable Web Applications
- AI Integrations
- Automation
- Linux Deployment
- Production Systems

---

<p align="center">

⭐ If you find VakilJui interesting, consider giving the repository a Star.

</p>
