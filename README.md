# Hotel Booking API

A comprehensive hotel booking system built with FastAPI, featuring JWT authentication, OAuth2 integration, PostgreSQL database, Redis caching, payment processing, and comprehensive monitoring.

## 🏨 Features

### Core Functionality

- **Hotel Management**: Full CRUD operations for hotels with amenities, images, and location data
- **Room Management**: Room types, availability calendar, pricing, and booking rules
- **User Management**: Registration, authentication, role-based access control (RBAC)
- **Booking System**: Real-time availability, conflict prevention, cancellation policies
- **Payment Processing**: Mock payment gateway integration with multiple payment methods
- **Review System**: Customer reviews and ratings with hotel responses

### Technical Features

- **Authentication & Authorization**: JWT tokens + OAuth2 + RBAC with Keycloak integration
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Caching**: Redis for performance optimization
- **API Design**: RESTful APIs with OpenAPI/Swagger documentation
- **Testing**: Comprehensive unit and integration tests with pytest
- **Monitoring**: OpenTelemetry, Prometheus metrics, Grafana dashboards
- **Containerization**: Docker and Docker Compose for easy deployment
- **Security**: Input validation, SQL injection prevention, rate limiting

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend/     │    │     FastAPI     │    │   PostgreSQL    │
│   Mobile App    │◄──►│   Application   │◄──►│    Database     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │     Redis       │    │    Keycloak     │
                       │     Cache       │    │   OAuth2 Server │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Prometheus    │    │     Grafana     │
                       │    Metrics      │◄──►│   Dashboards    │
                       └─────────────────┘    └─────────────────┘
```

### Layer Architecture

- **API Layer**: FastAPI routers with request/response validation
- **Service Layer**: Business logic and domain operations
- **Repository Layer**: Data access abstraction with caching
- **Model Layer**: SQLAlchemy models and Pydantic schemas
- **Core Layer**: Security, logging, monitoring, and utilities

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ (for direct database access)
- Redis 7+ (for caching)

### Development Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd python-hotel-booking
   ```

2. **Environment Configuration**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start Development Environment**

   ```bash
   # Start all services
   docker-compose -f docker-compose.dev.yml up -d

   # Or run locally
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

4. **Access the Application**
   - API Documentation: http://localhost:8001/docs
   - Health Check: http://localhost:8001/health
   - Grafana Dashboard: http://localhost:3000 (admin/admin123)
   - Prometheus Metrics: http://localhost:9090

### Production Deployment

1. **Configure Environment**

   ```bash
   # Update .env for production
   ENVIRONMENT=production
   DEBUG=false
   SECRET_KEY=your-strong-secret-key
   DATABASE_URL=postgresql://user:pass@host:port/db
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose up -d
   ```

## 📚 API Documentation

### Authentication Endpoints

```
POST /api/v1/auth/register     # User registration
POST /api/v1/auth/login        # User login
POST /api/v1/auth/logout       # User logout
POST /api/v1/auth/refresh      # Refresh token
GET  /api/v1/auth/me          # Current user profile
```

### Hotel Endpoints

```
GET    /api/v1/hotels                    # Search hotels
POST   /api/v1/hotels                    # Create hotel (Manager+)
GET    /api/v1/hotels/{hotel_id}         # Get hotel details
PUT    /api/v1/hotels/{hotel_id}         # Update hotel (Manager+)
DELETE /api/v1/hotels/{hotel_id}         # Delete hotel (Manager+)
GET    /api/v1/hotels/{hotel_id}/rooms   # Get hotel rooms
```

### Booking Endpoints

```
POST   /api/v1/bookings              # Create booking
GET    /api/v1/bookings              # User bookings
GET    /api/v1/bookings/{booking_id} # Get booking details
PUT    /api/v1/bookings/{booking_id} # Update booking
DELETE /api/v1/bookings/{booking_id} # Cancel booking
```

### Payment Endpoints

```
POST /api/v1/payments              # Process payment
GET  /api/v1/payments/{payment_id} # Get payment details
POST /api/v1/payments/{payment_id}/refund # Refund payment
```

## 🏛️ Database Schema

### Core Entities

- **Users**: Authentication, roles, profile information
- **Hotels**: Hotel details, location, amenities, images
- **Rooms**: Room types, pricing, availability, amenities
- **Bookings**: Reservations, guest details, status tracking
- **Payments**: Transaction records, payment methods, refunds
- **Reviews**: Customer feedback, ratings, hotel responses

### Key Relationships

- User → Bookings (1:N)
- Hotel → Rooms (1:N)
- Room → Bookings (1:N)
- Booking → Payments (1:N)
- Hotel → Reviews (1:N)
- User → Reviews (1:N)

## 🔐 Security Features

### Authentication & Authorization

- JWT tokens with refresh mechanism
- OAuth2 integration with Keycloak
- Role-based access control (Guest, Customer, Hotel Manager, Admin)
- Password hashing with bcrypt
- Session management

### API Security

- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy ORM
- CORS configuration
- Rate limiting
- Security headers
- Request/response logging

### Data Protection

- Environment variable configuration
- Sensitive data encryption
- Credit card number masking
- User data anonymization options

## 📊 Monitoring & Observability

### Metrics (Prometheus)

- HTTP request metrics (duration, count, status codes)
- Database query performance
- Cache hit/miss rates
- Business metrics (bookings, revenue)
- System metrics (CPU, memory, disk)

### Tracing (Jaeger)

- Distributed request tracing
- Database query tracing
- External service calls
- Error tracking and debugging

### Logging (Structured JSON)

- Request/response logging
- Security event logging
- Business operation logging
- Error tracking with context

### Dashboards (Grafana)

- Application performance metrics
- Business KPIs
- System health monitoring
- Alert management

## 🧪 Testing

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
│   ├── test_models.py
│   ├── test_services.py
│   └── test_repositories.py
└── integration/    # Integration tests for APIs
    ├── test_auth_api.py
    ├── test_hotel_api.py
    └── test_booking_api.py
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m auth
```

## 🏗️ Project Structure

```
hotel-booking-api/
├── app/
│   ├── api/v1/              # API route handlers
│   ├── core/                # Core utilities (security, cache, logging)
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic layer
│   ├── middleware/          # Custom middleware
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── docker/                  # Docker configuration
├── monitoring/              # Monitoring configuration
├── scripts/                 # Utility scripts
└── docs/                   # Additional documentation
```

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available configuration options:

- **Database**: PostgreSQL connection settings
- **Redis**: Cache configuration
- **JWT**: Token settings and secrets
- **OAuth2**: Keycloak integration
- **Monitoring**: Prometheus, Jaeger configuration
- **Email**: SMTP settings for notifications
- **File Upload**: Size limits and storage

### Feature Flags

- `DEBUG`: Enable debug mode and detailed error responses
- `CREATE_INITIAL_DATA`: Create sample data on startup
- `ENABLE_MONITORING`: Enable metrics collection
- `ENABLE_TRACING`: Enable distributed tracing

## 🚀 Deployment Options

### Docker Compose (Recommended)

Complete stack with all dependencies:

```bash
docker-compose up -d
```

### Kubernetes

Helm charts available in `k8s/` directory:

```bash
helm install hotel-booking ./k8s/helm-chart
```

### Cloud Platforms

- **AWS**: ECS/Fargate with RDS and ElastiCache
- **Google Cloud**: Cloud Run with Cloud SQL and Memorystore
- **Azure**: Container Instances with Azure Database

## 📈 Performance Considerations

### Caching Strategy

- User session caching
- Hotel search result caching
- Room availability caching
- Database query result caching

### Database Optimization

- Proper indexing on search columns
- Connection pooling
- Query optimization
- Read replicas for reporting

### API Performance

- Response compression
- Request/response size limiting
- Pagination for large datasets
- Async operations where applicable

## 🔮 Future Enhancements

### Planned Features

- Real-time notifications (WebSocket)
- Mobile app support (React Native)
- AI-powered recommendations
- Multi-language support
- Currency conversion
- Loyalty points system
- Advanced analytics dashboard

### Technical Improvements

- Event-driven architecture with message queues
- Microservices decomposition
- GraphQL API option
- Advanced caching strategies
- Automated deployment pipelines

## 🤝 Contributing

### Development Workflow

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with tests
4. Run test suite (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

### Code Standards

- Follow PEP 8 style guide
- Add type hints to all functions
- Write docstrings for all public methods
- Maintain test coverage above 80%
- Use meaningful commit messages

## 📞 Support

### Documentation

- API Documentation: `/docs` endpoint
- Architecture docs: `docs/architecture.md`
- Deployment guide: `docs/deployment.md`

### Issues & Support

- GitHub Issues for bug reports
- Discussions for feature requests
- Wiki for additional documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI framework and community
- SQLAlchemy ORM
- Redis for caching
- Prometheus & Grafana for monitoring
- Keycloak for authentication
- Docker for containerization

---

**Built with ❤️ for modern hotel booking systems**
