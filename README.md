# Mercator Document Library

A modern documentation platform built for both humans and AI agents. Create, edit, and collaborate on technical documentation with intelligent version control.

## 🚀 Features

- **Dual Access**: Optimized for both human users and AI agents
- **Collaborative Editing**: Real-time collaboration with version control
- **Smart Search**: Full-text and semantic search capabilities
- **AI Integration**: Native support for AI agent editing and management
- **Version Control**: Git-like versioning with conflict resolution
- **Modern UI**: Responsive design with dark mode support

## 📋 Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mercator_doc_library
```

### 2. Setup Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Infrastructure Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Elasticsearch (port 9200)
- MinIO (port 9000, console: 9001)
- ChromaDB (port 8001)

### 4. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### 5. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:3000

## 📁 Project Structure

```
mercator_doc_library/
├── docs/                    # Project documentation
│   ├── ARCHITECTURE.md     # System architecture
│   ├── API_SPEC.md         # API specification
│   └── DATABASE_SCHEMA.md  # Database schema
├── frontend/               # Next.js frontend
│   ├── app/               # App Router pages
│   ├── components/        # React components
│   ├── lib/               # Utilities
│   └── stores/            # State management
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Core configuration
│   │   ├── models/       # Database models
│   │   └── schemas/      # Pydantic schemas
│   └── requirements.txt
├── docker-compose.yml     # Docker services
└── .env.example          # Environment variables
```

## 🔧 Development

### Backend Development

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🗄️ Database Migration

```bash
cd backend
alembic upgrade head
```

## 🐳 Docker Deployment

### Build and Run

```bash
docker-compose up --build
```

### Stop Services

```bash
docker-compose down
```

### Clear All Data

```bash
docker-compose down -v
```

## 🔐 Security

- JWT-based authentication
- API key authentication for AI agents
- Rate limiting
- CORS protection
- Password hashing (bcrypt)
- SQL injection prevention (SQLAlchemy ORM)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For support, please open an issue in the repository.

## 🗺️ Roadmap

- [ ] Real-time collaborative editing
- [ ] Advanced semantic search
- [ ] AI-powered content suggestions
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Advanced analytics

---

Built with ❤️ using Next.js, FastAPI, and PostgreSQL
