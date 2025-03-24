# ReportEase: Accessibility Issue Reporting Platform

A Django-based web application for reporting, tracking, and managing accessibility issues. Users can report issues with location data, upvote existing issues, and track resolution progress by agencies.

## Installation

### Prerequisites
- Python 3.8+
- pip
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fyp-project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a `.env` file in the project root** with the following variables:
   ```
   SECRET_KEY=your_django_secret_key
   MAPBOX_ACCESS_TOKEN=your_mapbox_token
   OPENAI_API_KEY=your_openai_api_key
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create initial agency data**
   ```bash
   python manage.py add_agencies
   ```

8. **Create a superuser for admin access**
   ```bash
   python manage.py createsuperuser
   ```

## Running the Application

1. **Start the development server**
   ```bash
   python manage.py runserver
   ```

2. **Access the application**
   - Open your browser and go to: `http://127.0.0.1:8000/`
   - Admin interface: `http://127.0.0.1:8000/admin/`

## Running Tests

This project uses Factory Boy to generate test data and Django's test framework for running tests.

1. **Run all tests**
   ```bash
   python manage.py test fypapp
   ```

2. **Run specific test modules**
   ```bash
   python manage.py test fypapp.tests.test_views
   python manage.py test fypapp.tests.test_api
   python manage.py test fypapp.tests.test_create_issue
   ```

### Test Coverage

The test suite includes:
- API endpoint tests (authentication, issue creation, upvoting)
- View tests (page rendering, authentication)
- Issue creation workflow tests
- Validation tests for models

## Features

- **Issue Reporting**: Users can report accessibility issues with location data
- **Interactive Maps**: View issues on an interactive map using Mapbox
- **Voice Input**: Record and transcribe issue descriptions using OpenAI
- **Upvoting System**: Users can upvote important issues
- **Agency Assignment**: Issues can be assigned to responsible agencies
- **Status Tracking**: Track the resolution progress of reported issues
- **REST API**: Complete API for all functionality

## Deployment

This application is configured for deployment to Heroku:

1. **Install Heroku CLI**
   ```bash
   # Follow instructions at: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create a Heroku app**
   ```bash
   heroku create your-app-name
   ```

4. **Configure environment variables**
   ```bash
   heroku config:set SECRET_KEY=your_django_secret_key
   heroku config:set MAPBOX_ACCESS_TOKEN=your_mapbox_token
   heroku config:set OPENAI_API_KEY=your_openai_api_key
   ```

5. **Push to Heroku**
   ```bash
   git push heroku main
   ```

6. **Run migrations on Heroku**
   ```bash
   heroku run python manage.py migrate
   ```

7. **Create a superuser on Heroku**
   ```bash
   heroku run python manage.py createsuperuser
   ```

8. **Initialize agencies on Heroku**
   ```bash
   heroku run python manage.py add_agencies
   ```

## Technologies

- Django
- Django REST Framework
- Mapbox GL JS
- OpenAI API (Whisper for transcription, GPT-4 for processing)
- Bootstrap 5
- Factory Boy (testing)
- Heroku (deployment)


Author: Leong Wen Xuan 