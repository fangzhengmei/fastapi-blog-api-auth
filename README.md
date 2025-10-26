# 🚀 FastAPI Blog CRUD with Authentication (SQLite)

A lightweight **FastAPI Blog API** implementing **CRUD operations**, **JWT authentication**, and an **SQLite database**.
Includes Swagger API docs, password hashing, and modular project structure.
This project is perfect for learning FastAPI fundamentals and showcasing API development skills.

-----

## 📌 Features

  - ✅ User registration & login (JWT authentication)
  - ✅ CRUD operations on blogs (Create, Read, Update, Delete)
  - ✅ Password hashing & verification
  - ✅ Simple SQLite database (file-based, no external setup required)
  - ✅ API documentation with Swagger UI (`/docs`)
  - ✅ Modular project structure with routers and repositories

-----

## 🛠️ Tech Stack

  - **Backend:** FastAPI
  - **Database:** SQLite
  - **Validation:** Pydantic
  - **Authentication:** JWT (JSON Web Tokens)
  - **Password Security:** Passlib (bcrypt)

-----

## 🚀 Getting Started

### 1️⃣ Prerequisites

  - Python 3.8+

### 2️⃣ Clone Repository

```bash
git clone https://github.com/rajatjain3366/fastapi-blog-api-auth.git
cd fastapi-blog-api-auth
```

### 3️⃣ Setup Environment & Install Dependencies

Create and activate a virtual environment:

```bash
# For MacOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

Install the required packages from your `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 4️⃣ Run the Application

Start the FastAPI server using Uvicorn. (Note: We point to `blog.main:app` because your `main.py` is inside the `blog` directory).

```bash
uvicorn blog.main:app --reload
```

The `--reload` flag automatically restarts the server when you make code changes.

### 5️⃣ Access the API

Your API is now running\!

  - **API URL:** `http://127.0.0.1:8000`
  - **Swagger Docs:** `http://127.0.0.1:8000/docs`

-----

## ⚙️ Configuration

This project uses a `.env` file for configuration, which is necessary for JWT authentication.

1.  Create a file named `.env` in the project's root directory (at the same level as `requirements.txt`).
2.  Add the following variables. You can generate a strong secret key using the command: `openssl rand -hex 32`

<!-- end list -->

```ini
# .env file
SECRET_KEY="YOUR_SUPER_STRONG_SECRET_KEY_HERE"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

*(**Note:** Ensure your code is set up to read these environment variables, for example, using `pydantic-settings`.)*

-----

## 🌐 API Endpoints

Here is a brief overview of the available endpoints. For full details, visit `/docs`.

### Authentication

  - `POST /login`: Authenticate a user and receive a JWT access token.

### Users

  - `POST /users`: Register a new user.
  - `GET /users/{id}`: Get user details by ID.

### Blogs

  - `POST /blogs`: Create a new blog post (Requires authentication).
  - `GET /blogs`: Get a list of all blog posts.
  - `GET /blogs/{id}`: Get a specific blog post by ID.
  - `PUT /blogs/{id}`: Update a blog post (Requires authentication).
  - `DELETE /blogs/{id}`: Delete a blog post (Requires authentication).