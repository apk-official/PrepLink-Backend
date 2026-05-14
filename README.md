#  PrepLink

> **AI-powered interview preparation platform**  
> Structured, personalised, and focused interview prep — all in one place.
---

##Project Status: In Active Development

PrepLink is currently **under development**.  
Core authentication, backend architecture, and data models are being actively built.

Features, UI, and APIs are evolving rapidly — expect breaking changes.

---

## What is PrepLink?

PrepLink is an **AI-assisted interview preparation platform** designed to help candidates:

- Organise interview prep by **company & role**
- Practice **custom interview questions**
- Get structured, role-specific insights instead of generic prep material

The goal is to move beyond generic Q&A — and provide a **centralised, intelligent prep workspace**.

---

## Problem It Solves

Most candidates get generic AI interview prep with little company or role context.

### PrepLink solves this by:
**PrepLink** creates **company- and role-specific interview preparation** by combining:
- Job description
- Candidate resume
- Company specific data

This results in tailored **interview questions & answers, preparation tips, and company insights** — instead of generic AI responses.


---

## Current Architecture (Early)

### Backend
- **FastAPI** (Python)
- **PostgreSQL**
- **SQLAlchemy**
- **JWT Authentication**
- **Google OAuth**
- Service-based architecture (clean separation of concerns)

### Frontend

👉 **[View Frontend Repository](https://github.com/apk-official/Preplink-Frontend)**

---
##  Authentication (Implemented)

- Google OAuth login
- JWT-based session handling
- Secure protected APIs

---

##  Core Concepts (Planned)

- Interview prep projects (company + role)
- Tailored Question & answer
- AI-assisted suggestions

---

##  Tech Stack

- **Python 3.7**
- **FastAPI**
- **PostgreSQL**
- **SQLAlchemy**
- **Pydantic**
- **JWT**
- **Google OAuth**
- **Docker** *(planned)*

---

##  Repository Structure (Backend)
app/   
├── api/  # Route definitions  
├── core/ # Config, security, dependencies  
├── db/ # DB session & helpers  
├── models/ # SQLAlchemy models  
├── services/ # Business logic  
├──utils/ #Utilities  
└── main.py # Application entry point
---

##  Getting Started (Development)

> Detailed setup instructions will be added once the backend stabilizes.

For now:
- Clone the repo
- Set up `.env`
- Run FastAPI with Uvicorn
- PostgreSQL required

---
##  Roadmap (High-Level)

- [x] Backend foundation
- [x] Google authentication
- [x] User management
- [x] Interview project model
- [x] Question & answer workflows
- [x] AI integration
- [ ] Deployment & CI

---

##  Contributing

PrepLink is currently a **personal / early-stage project**.  
Contribution guidelines will be added later.

---
