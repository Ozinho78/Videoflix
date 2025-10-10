# 🎬 Backend Project for Videoflix (Django REST Framework)

This is the **backend** for the **Videoflix App**, built with **Django** and **Django REST Framework (DRF)**.  
It powers a full-featured video platform where users can upload and stream videos in multiple resolutions.  
The backend provides a REST API for a VanillaJS frontend and runs completely inside Docker.

---

## 🚀 Features

### 🔐 User Authentication
- Registration with email verification link  
- Login, logout, and JWT authentication  
- Password reset via email (token-based confirmation)  
- Custom validators for email format, uniqueness, and password strength

### 🎥 Video Management
- Upload videos via Django Admin  
- Automatic transcoding to `480p`, `720p`, and `1080p` using **FFmpeg**  
- HLS streaming support (`index.m3u8` + TS segments)  
- Redis Queue (RQ) worker for background video processing  

### ⚙️ API Architecture
- RESTful endpoints for authentication and video streaming  
- JWT authentication with HTTP-only cookies  
- CORS enabled for local frontend integration (`http://127.0.0.1:5500`)

--------

## 🧱 Technology Stack

| Component | Technology |
|------------|-------------|
| **Framework** | Django 5.x, Django REST Framework |
| **Database** | PostgreSQL (Docker container) |
| **Task Queue** | Redis + Django RQ |
| **Transcoding** | FFmpeg (installed in container) |
| **Web Server** | Gunicorn |
| **Static Files** | WhiteNoise |
| **Testing** | Pytest |
| **Deployment** | Docker Compose |
| **Frontend** | VanillaJS (localhost:5500) |

-------------------------------------------------------------------------------------------------------------

## ⚡️ Quickstart (for Windows, macOS, or Linux)

### ✅ Requirements
Before starting, make sure you have:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and **running**
- Git installed (`git --version`)
- Internet connection (for first-time Docker image downloads)

---

## Installation

## 🐳 Run with Docker

### 1. Clone the repository
```bash
git clone https://github.com/Ozinho78/videoflix.git
cd videoflix
```


### 2. Create .env file
```bash
DEBUG=True
SECRET_KEY=your_secret_key_here

DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=supersecretpassword
DB_HOST=db
DB_PORT=5432

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=adminpassword

ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:5500

REDIS_HOST=redis
REDIS_PORT=6379
```


### 3. Build and start all services
```bash
docker compose up --build
```

This will:
 - Build the Django backend image
 - Start PostgreSQL and Redis containers
 - Wait for the database
 - Run migrate, collectstatic, and create a superuser
 - Start the Gunicorn web server

Access the API at:
👉 http://127.0.0.1:8000/api/

Access the Admin at:
👉 http://127.0.0.1:8000/admin/



### 🐋 Manually Build & Push Docker Image

If you want to deploy or publish your backend image on Docker Hub:

### 1. Build image
```bash
docker build -t ozinho78/videoflix-backend:latest .
```

### 2. Test locally
```bash
docker run -p 8000:8000 ozinho78/videoflix-backend:latest
```

### 3. Push to Docker Hub
```bash
docker login
docker push ozinho78/videoflix-backend:latest
```

### Example Endpoints
 - POST	  /api/register/	                                Register new user
 - POST	  /api/login/	                                    Login with JWT
 - POST	  /api/logout/	                                  Logout user
 - POST	  /api/password_reset/	                          Send password reset link
 - POST	  /api/password_confirm/<uidb64>/<token>/	        Confirm new password
 - GET	  /api/video/<movie_id>/<resolution>/index.m3u8	  Get video playlist
 - GET	  /api/video/<movie_id>/<resolution>/<segment>/	  Get TS segment


### 🧰 Common Docker Commands

### Run migrations manually:
```bash
docker compose exec web python manage.py migrate
```

### Create superuser manually:
```bash
docker compose exec web python manage.py createsuperuser
```

### Run tests:
```bash
docker compose exec web pytest
```

### Tail logs:
```bash
docker compose logs -f web
```

### 🧠 Alternative: Run Without Docker (Local Setup)
### 1. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate     # macOS / Linux
venv\Scripts\activate        # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure SQLite in .env
```bash
DEBUG=True
SECRET_KEY=your_local_secret
DB_NAME=db.sqlite3
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:5500
```

### 4. Apply migrations and create superuser
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Start local server
```bash
python manage.py runserver
```


### Visit:
👉 http://127.0.0.1:8000/api/

### 📦 Stop or Rebuild Containers

Stop containers:
```bash
docker compose down
```

Rebuild clean:
```bash
docker compose down -v --rmi all --remove-orphans
docker compose up --build
```