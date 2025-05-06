# Project Structure

```
Darati/
├── backend/
│   ├── database.py           # Database connection and session management
│   ├── main.py              # FastAPI application entry point
│   ├── models.py            # SQLAlchemy models (Audiobook, Chapter, etc.)
│   ├── routes/
│   │   ├── upload_routes.py # Handles audio file uploads and chapter management
│   │   └── user_books_routes.py # Manages user-specific book operations
│   ├── utils/
│   │   └── azure_storage.py # Azure Blob Storage integration
│   └── venv_new/            # Python virtual environment
│
├── frontend/
│   ├── screens/
│   │   ├── uploadScreen.js  # Main upload interface with chapter management
│   │   └── ...              # Other screen components
│   ├── components/          # Reusable UI components
│   ├── navigation/          # Navigation configuration
│   └── ...                 # Other frontend files
│
├── .env                    # Environment variables
└── project_structure.md    # This file
```

## Backend Structure

### Core Files
- `main.py`: FastAPI application setup and router configuration
- `database.py`: Database connection and session management
- `models.py`: SQLAlchemy models for database tables

### Routes
- `upload_routes.py`: Handles:
  - Audio file uploads
  - Chapter management
  - Book creation
  - Azure storage integration
- `user_books_routes.py`: Manages:
  - User-specific book retrieval
  - Admin access control
  - Book filtering

### Utils
- `azure_storage.py`: Azure Blob Storage operations:
  - File upload
  - Container management
  - URL generation

## Frontend Structure

### Screens
- `uploadScreen.js`: Main upload interface with:
  - File selection
  - Chapter management
  - Category selection
  - Book selection
  - Upload progress tracking

### Components
- Reusable UI components for:
  - Buttons
  - Inputs
  - Pickers
  - Progress indicators

### Navigation
- Screen navigation configuration
- Route management

## Environment Configuration
- `.env`: Contains:
  - Database credentials
  - Azure storage connection strings
  - API configuration
  - Other environment-specific settings 