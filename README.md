# TutorPro - Preply Clone

A comprehensive Flask-based online tutoring platform inspired by Preply.com, featuring advanced course management, payment processing, video conferencing, and more.

## Screenshots

![Homepage](TutorPro-Home.png "Homepage")

## Features

### Core Platform Features

- **User Management**: Three-role system (Learner, Tutor, Admin) with comprehensive profiles
- **Authentication**: Secure login, registration, password hashing, and session management
- **Course Management**: Full-featured course creation, syllabus tracking, and enrollment
- **Booking System**: Advanced scheduling with availability management and calendar integration
- **Payment Processing**: Multi-gateway support (UPI via Razorpay, PayPal) with secure transactions
- **Video Conferencing**: Zoom and Google Meet integration with meeting management
- **Demo Classes**: Complete demo class scheduling and feedback system
- **Job Board**: Tutoring opportunity postings and application management
- **Notifications**: Comprehensive email and in-app notification system
- **Reviews & Ratings**: Multi-dimensional rating and review system

### Advanced Features

- **Assignment System**: Assignment creation, submission handling, and grading
- **Quiz System**: Interactive quizzes with multiple question types
- **Progress Tracking**: Student progress analytics and achievement system
- **Discussion Boards**: Course-specific discussion forums and Q&A
- **File Management**: Secure file uploads for materials and assignments
- **Analytics**: Comprehensive reporting and business intelligence
- **Gamification**: Achievement badges, certificates, and progress rewards
- **Admin Dashboard**: Complete platform management and oversight

## Technology Stack

### Backend

- **Framework**: Flask with modular blueprint architecture
- **Database**: SQLite for development (PostgreSQL migration ready)
- **ORM**: SQLAlchemy with comprehensive model relationships
- **Authentication**: Flask-Login with role-based access control
- **Forms**: Flask-WTF with CSRF protection
- **Migrations**: Flask-Migrate for database versioning
- **Email**: Flask-Mail for notification system
- **Caching**: Flask-Caching for performance optimization

### Frontend

- **Templates**: Jinja2 with responsive Bootstrap 5 design
- **JavaScript**: jQuery for dynamic interactions and AJAX
- **UI Components**: Bootstrap 5 with custom enhancements
- **Charts**: Chart.js for analytics visualization
- **Date/Time**: Flatpickr for scheduling interfaces

### Payment & Integration

- **UPI**: Razorpay SDK for Indian market
- **PayPal**: PayPal Checkout SDK for international payments
- **Video**: Zoom SDK and Google Meet API
- **File Storage**: Local storage with cloud migration path

### Security

- **Authentication**: Werkzeug password hashing
- **CSRF**: Flask-WTF CSRF protection
- **Validation**: Input validation and sanitization
- **Rate Limiting**: API endpoint protection
- **Fraud Detection**: Advanced payment security measures

## Project Structure

```
tutorPro/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── user.py              # User, UserProfile, LearnerProfile
│   │   ├── tutor.py             # TutorProfile
│   │   ├── course.py            # Course, Syllabus, Assignment, Quiz
│   │   ├── booking.py           # Booking, Availability, MeetingLink
│   │   ├── payment.py           # Payment, Transaction, Payout
│   │   ├── review.py            # Review, Rating
│   │   ├── job.py              # JobPost, JobApplication
│   │   ├── notification.py      # Notification, EmailLog
│   │   ├── meeting.py           # Meeting, MeetingParticipant
│   │   └── demo.py             # DemoClass, DemoFeedback
│   ├── auth/                    # Authentication blueprint
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── main/                    # Main application blueprint
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── tutor/                   # Tutor-specific blueprint
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   ├── routes.py
│   │   ├── profile.py
│   │   ├── availability.py
│   │   ├── bookings.py
│   │   └── demos.py
│   ├── student/                 # Student-specific blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── admin/                   # Admin blueprint
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── course/                  # Course management blueprint
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── payment/                 # Payment processing blueprint
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   ├── routes.py
│   │   ├── paypal.py
│   │   ├── upi.py
│   │   ├── payouts.py
│   │   ├── analytics.py
│   │   └── security.py
│   ├── meeting/                 # Video conferencing blueprint
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   ├── routes.py
│   │   └── management.py
│   ├── demo/                    # Demo class blueprint
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   ├── api/                     # RESTful API endpoints
│   │   ├── __init__.py
│   │   ├── payment.py
│   │   ├── course.py
│   │   ├── tutor.py
│   │   └── meeting.py
│   ├── services/                # Business logic services
│   │   ├── __init__.py
│   │   ├── calendar_integration.py
│   │   ├── google_meet_integration.py
│   │   └── zoom_integration.py
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py
│   │   ├── decorators.py
│   │   ├── error_handlers.py
│   │   ├── file_utils.py
│   │   └── meeting_security.py
│   ├── static/                  # Static files
│   │   ├── css/
│   │   │   └── responsive.css
│   │   ├── js/
│   │   │   ├── automated-reminders.js
│   │   │   ├── conflict-detection.js
│   │   │   ├── drag-drop-reschedule.js
│   │   │   ├── recurring-bookings.js
│   │   │   └── timezone-support.js
│   │   └── images/
│   └── templates/               # Jinja2 templates
│       ├── base.html
│       ├── auth/
│       ├── main/
│       ├── tutor/
│       ├── student/
│       ├── admin/
│       ├── course/
│       ├── payment/
│       ├── meeting/
│       ├── demo/
│       └── errors/
├── config/                      # Configuration files
│   ├── __init__.py
│   ├── development.py
│   ├── production.py
│   └── testing.py
├── migrations/                  # Database migrations
├── tests/                       # Test files
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables example
├── .env.payment.example         # Payment configuration example
├── .gitignore                   # Git ignore file
├── run.py                       # Application runner
├── wsgi.py                      # WSGI entry point
├── architecture_plan.md          # Original architecture documentation
├── ARCHITECTURE_ANALYSIS.md     # Implementation analysis
├── IMPLEMENTATION_ROADMAP.md     # Future development roadmap
├── COURSE_IMPLEMENTATION_SUMMARY.md  # Course system documentation
├── PAYMENT_IMPLEMENTATION.md     # Payment system documentation
├── README.md                    # This file
└── features.md                  # Comprehensive feature list
```

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd tutorPro
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   ```bash
   cp .env.example .env
   cp .env.payment.example .env.payment
   # Edit .env and .env.payment with your configuration
   ```

5. Initialize the database:

   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. Run the application:
   ```bash
   python run.py
   ```

The application will be available at `http://localhost:5000`.

## Default Admin Account

The system automatically creates an admin account during the first run:

- Email: `admin@tutorpro.com`
- Password: `Admin123!`

## User Roles

- **Learner**: Can search for tutors, book sessions, enroll in courses, and track progress
- **Tutor**: Can create profiles, set availability, manage bookings, create courses, and track earnings
- **Admin**: Has full access to the platform for user management, content oversight, and analytics

## Configuration

The application uses environment-specific configuration files:

- `config/development.py`: Development settings
- `config/production.py`: Production settings
- `config/testing.py`: Testing settings

### Environment Variables

Key environment variables to configure:

```bash
# Basic Configuration
SECRET_KEY=your-secret-key
FLASK_ENV=development

# Database
SQLALCHEMY_DATABASE_URI=sqlite:///tutorPro_dev.db

# Email Configuration
MAIL_SERVER=smtp.googlemail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Payment Configuration (see .env.payment.example)
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# Meeting Integration
GOOGLE_MEET_CREDENTIALS_FILE=path/to/credentials.json
ZOOM_API_KEY=your-zoom-api-key
ZOOM_API_SECRET=your-zoom-api-secret
```

## Database

The application uses SQLite for development by default. For production, you can switch to PostgreSQL by updating the `SQLALCHEMY_DATABASE_URI` in your environment configuration:

```bash
SQLALCHEMY_DATABASE_URI=postgresql://username:password@localhost/tutorpro
```

## Security Features

- **Authentication**: Secure password hashing with Werkzeug
- **Session Management**: Flask-Login with secure session handling
- **CSRF Protection**: Flask-WTF with token validation
- **Role-Based Access Control**: Decorators for route protection
- **Input Validation**: Comprehensive validation and sanitization
- **Rate Limiting**: API endpoint protection
- **Fraud Detection**: Advanced payment security measures
- **File Upload Security**: Type validation and secure storage

## Key Features Overview

### 🎓 Course Management

- Create and manage structured courses
- Syllabus tracking with topic progression
- Assignment and quiz system
- Progress analytics and reporting
- Achievement and certification system

### 💳 Payment System

- Multi-gateway support (UPI, PayPal, Cards)
- Secure transaction processing
- Tutor payout management
- Comprehensive analytics
- Refund processing

### 📅 Booking & Scheduling

- Tutor availability management
- Real-time booking system
- Calendar integration
- Meeting link generation
- Automated reminders

### 🎥 Video Conferencing

- Zoom integration for meetings
- Google Meet support
- Meeting recording management
- Calendar synchronization
- Virtual whiteboard tools

### 💼 Job Board

- Tutoring opportunity postings
- Application tracking system
- Job search and filtering
- Communication tools
- Application management

### 📊 Analytics & Reporting

- Learning progress analytics
- Business intelligence dashboards
- Revenue tracking
- User engagement metrics
- Exportable reports

## API Documentation

The platform provides RESTful API endpoints for:

- User authentication and management
- Course operations
- Booking and scheduling
- Payment processing
- Notification management
- Analytics data

API documentation is available in the [`ARCHITECTURE_ANALYSIS.md`](ARCHITECTURE_ANALYSIS.md) and individual implementation documents.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`python -m pytest`)
6. Submit a pull request

## Development Guidelines

- Follow PEP 8 for code style
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints where appropriate
- Follow the existing code patterns and architecture

## Deployment

### Production Deployment

1. Set environment variables for production
2. Configure PostgreSQL database
3. Set up Redis for caching
4. Configure SSL certificates
5. Set up reverse proxy (Nginx)
6. Use Gunicorn as WSGI server

### Docker Deployment

```bash
# Build the image
docker build -t tutorpro .

# Run the container
docker run -p 5000:5000 --env-file .env tutorpro
```

## Monitoring and Maintenance

- **Application Logs**: Check `logs/` directory for application logs
- **Error Tracking**: Comprehensive error handling and logging
- **Performance Monitoring**: Built-in performance metrics
- **Security Monitoring**: Fraud detection and security alerts

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and documentation:

- **Architecture Documentation**: [`architecture_plan.md`](architecture_plan.md)
- **Implementation Analysis**: [`ARCHITECTURE_ANALYSIS.md`](ARCHITECTURE_ANALYSIS.md)
- **Future Roadmap**: [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md)
- **Payment System**: [`PAYMENT_IMPLEMENTATION.md`](PAYMENT_IMPLEMENTATION.md)
- **Course System**: [`COURSE_IMPLEMENTATION_SUMMARY.md`](COURSE_IMPLEMENTATION_SUMMARY.md)
- **Feature List**: [`features.md`](features.md)

## Version History

- **v1.0.0**: Initial release with core platform features
- **v1.1.0**: Enhanced course management and analytics
- **v1.2.0**: Advanced payment system and security
- **v1.3.0**: Video conferencing integration
- **v2.0.0**: Complete platform with all advanced features

---

**Current Implementation Status**: ✅ Production Ready with Comprehensive Feature Set

The TutorPro platform is a fully-featured online tutoring solution that exceeds the original Preply.com clone requirements with advanced course management, payment processing, video conferencing, and analytics capabilities.
