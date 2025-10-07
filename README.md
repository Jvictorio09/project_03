# myProject

A basic Django project with a simple app called `myApp`.

## Project Structure

```
myProject/
├── manage.py
├── requirements.txt
├── README.md
├── myProject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── myApp/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── tests.py
    ├── urls.py
    └── views.py
```

## Setup Instructions

1. **Install Django:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

3. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

4. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

5. **Access your application:**
   - Home page: http://127.0.0.1:8000/
   - About page: http://127.0.0.1:8000/about/
   - Admin panel: http://127.0.0.1:8000/admin/

## Features

- Basic Django project structure
- Simple home and about pages
- Admin interface ready
- SQLite database configured
- Basic URL routing

## Next Steps

- Add models to `myApp/models.py`
- Create templates in `myApp/templates/`
- Add more views and functionality
- Customize the admin interface
"# project_03" 
