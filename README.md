# Task Manager Flask Application

A Flask-based task management application with both web interface and REST API.

## Features

- User authentication (register, login, logout)
- Task management (create, read, update, delete)
- Task prioritization
- Due date tracking
- REST API with Swagger documentation

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Initialize the database:
```bash
python init_db.py
```

## Running the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`
API documentation will be available at `http://localhost:5000/api/docs`

## REST API Documentation

The application provides a REST API for task management. All API endpoints require authentication.

### Authentication

The API uses session-based authentication. You need to log in through the web interface before using the API.

### API Endpoints

#### Tasks

- `GET /tasks/` - List all tasks
  - Returns: Array of task objects
  - Status codes: 200 (Success), 401 (Unauthorized)

- `POST /tasks/` - Create a new task
  - Request body: 
    ```json
    {
        "content": "Task description",
        "due_date": "YYYY-MM-DD",  // Optional
        "priority_id": 1  // Optional
    }
    ```
  - Returns: Created task object
  - Status codes: 201 (Created), 400 (Bad Request), 401 (Unauthorized)

- `GET /tasks/<id>` - Get a specific task
  - Returns: Task object
  - Status codes: 200 (Success), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found)

- `PUT /tasks/<id>` - Update a task
  - Request body:
    ```json
    {
        "content": "Updated description",
        "completed": 1,
        "due_date": "YYYY-MM-DD",
        "priority_id": 1
    }
    ```
  - Returns: Updated task object
  - Status codes: 200 (Success), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found)

- `DELETE /tasks/<id>` - Delete a task
  - Status codes: 204 (No Content), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found)

- `POST /tasks/<id>/toggle` - Toggle task completion status
  - Returns: Updated task object
  - Status codes: 200 (Success), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found)

### Response Objects

#### Task Object

```json
{
    "id": 1,
    "content": "Task description",
    "completed": 0,
    "date_created": "2024-01-01T12:00:00",
    "due_date": "2024-12-31",
    "priority_id": 1
}
```

## Testing

To run the tests:

```bash
pytest
```

To run tests with coverage report:

```bash
pytest --cov=app tests/
```

## License

This project is licensed under the MIT License.
