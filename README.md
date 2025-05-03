# Date Mate Application

This is a FastAPI-based backend application that combines APIs for Match Making, Dating Advisor, and Notifications.

## Prerequisites

- Python 3.8 or higher installed on your system
- Git (optional, for cloning the repository)

## Setup Instructions

### 1. Clone the repository (if you haven't already)

```bash
git clone https://github.com/syeda-ai-dev/Dating-App.git
cd Dating-App
```

### 2. Create and activate a virtual environment

It is recommended to use a virtual environment to manage dependencies.

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create a `.env` file in the root directory

Create a `.env` file to store environment variables required by the application. Example:

```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_ENDPOINT=your_openai_endpoint_here
MODEL=gpt-3.5-turbo
DB_BASE_URL=your_database_url_here
```

Replace the values with your actual credentials and endpoints.

### 5. Run the application

Use `uvicorn` to run the FastAPI app with auto-reload enabled:

```bash
uvicorn mhire.com.main:app --reload
```

By default, the app will be available at `http://127.0.0.1:8000`.

### 6. API Documentation

Once the app is running, you can access the interactive API docs at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Postman: `http://127.0.0.1:8000/particular-endpoint-name`

## Project Structure

- `mhire/com/main.py`: Main FastAPI app instance and router inclusion
- `mhire/com/app/match_making/`: Match making related API routes and logic
- `mhire/com/app/date_mate/`: Dating advisor related API routes and logic
- `mhire/com/app/notification/`: Notification related API routes and logic
- `mhire/com/config/config.py`: Configuration and environment variable loading

## Logging

The application uses Python's logging module configured to output INFO level logs to the console.
