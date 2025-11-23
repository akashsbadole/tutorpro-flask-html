# TutorPro API Documentation

## Overview

The TutorPro API provides comprehensive functionality for the tutor marketplace platform, including user management, course enrollment, booking, payments, and more.

## Base URL

```
https://api.tutorpro.com/v1
```

## Authentication

Most API endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Rate Limiting

API requests are limited to 1000 requests per hour per user.

## Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {},
  "message": "Success",
  "timestamp": "2025-11-18T10:00:00Z"
}
```

## Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {}
  },
  "timestamp": "2025-11-18T10:00:00Z"
}
```

## API Endpoints

### Authentication

#### POST /auth/login
Login user and return JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "role": "student"
    },
    "expires_in": 3600
  }
}
```

#### POST /auth/register
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe",
  "role": "student"
}
```

#### POST /auth/refresh
Refresh JWT token.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

### Users

#### GET /users/profile
Get current user profile.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "role": "student",
    "profile": {
      "bio": "Passionate learner",
      "location": "New York",
      "avatar": "https://example.com/avatar.jpg"
    }
  }
}
```

#### PUT /users/profile
Update user profile.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "name": "John Smith",
  "bio": "Updated bio",
  "location": "Boston"
}
```

### Tutors

#### GET /tutors
Search and filter tutors.

**Query Parameters:**
- `subject` (string): Subject to filter by
- `location` (string): Location to filter by
- `price_min` (number): Minimum hourly rate
- `price_max` (number): Maximum hourly rate
- `rating_min` (number): Minimum rating
- `online_only` (boolean): Filter for online tutors only
- `page` (number): Page number (default: 1)
- `limit` (number): Results per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": {
    "tutors": [
      {
        "id": 1,
        "name": "Jane Smith",
        "subjects": ["Mathematics", "Physics"],
        "hourly_rate": 50,
        "rating": 4.8,
        "location": "New York",
        "online": true,
        "avatar": "https://example.com/avatar.jpg"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "pages": 8
    }
  }
}
```

#### GET /tutors/{id}
Get tutor details by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Jane Smith",
    "bio": "Experienced math tutor with 10+ years of teaching",
    "subjects": ["Mathematics", "Physics"],
    "hourly_rate": 50,
    "rating": 4.8,
    "review_count": 127,
    "location": "New York",
    "online": true,
    "availability": [
      {
        "day": "Monday",
        "slots": ["9:00-10:00", "14:00-15:00"]
      }
    ],
    "education": [
      {
        "degree": "M.S. Mathematics",
        "institution": "MIT",
        "year": 2010
      }
    ],
    "certifications": [
      {
        "name": "Teaching Certification",
        "issuer": "State Board of Education",
        "year": 2012
      }
    ]
  }
}
```

### Courses

#### GET /courses
List available courses.

**Query Parameters:**
- `subject` (string): Subject to filter by
- `level` (string): Course level (beginner, intermediate, advanced)
- `price_min` (number): Minimum price
- `price_max` (number): Maximum price
- `online_only` (boolean): Filter for online courses only
- `page` (number): Page number
- `limit` (number): Results per page

**Response:**
```json
{
  "success": true,
  "data": {
    "courses": [
      {
        "id": 1,
        "title": "Introduction to Calculus",
        "description": "Learn the fundamentals of calculus",
        "instructor": {
          "id": 1,
          "name": "Jane Smith"
        },
        "subject": "Mathematics",
        "level": "beginner",
        "price": 199,
        "duration": "8 weeks",
        "enrollment_count": 45,
        "rating": 4.7,
        "image": "https://example.com/course.jpg"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 50,
      "pages": 3
    }
  }
}
```

#### GET /courses/{id}
Get course details by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Introduction to Calculus",
    "description": "Learn the fundamentals of calculus...",
    "instructor": {
      "id": 1,
      "name": "Jane Smith",
      "bio": "Experienced math tutor...",
      "rating": 4.8
    },
    "subject": "Mathematics",
    "level": "beginner",
    "price": 199,
    "duration": "8 weeks",
    "enrollment_count": 45,
    "rating": 4.7,
    "review_count": 23,
    "syllabus": [
      {
        "week": 1,
        "title": "Limits and Continuity",
        "topics": ["Understanding limits", "Continuity"]
      }
    ],
    "requirements": ["Basic algebra knowledge"],
    "learning_objectives": ["Understand calculus fundamentals"],
    "image": "https://example.com/course.jpg",
    "youtube_playlist": {
      "id": "PLxxxxxx",
      "title": "Calculus Supplementary Videos"
    }
  }
}
```

#### POST /courses/{id}/enroll
Enroll in a course.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "enrollment_id": 123,
    "course_id": 1,
    "enrollment_date": "2025-11-18T10:00:00Z",
    "status": "active",
    "payment_status": "completed"
  }
}
```

### Bookings

#### GET /bookings
Get user's bookings.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Query Parameters:**
- `status` (string): Filter by status (upcoming, completed, cancelled)
- `type` (string): Filter by type (session, demo)
- `page` (number): Page number
- `limit` (number): Results per page

**Response:**
```json
{
  "success": true,
  "data": {
    "bookings": [
      {
        "id": 1,
        "tutor": {
          "id": 1,
          "name": "Jane Smith"
        },
        "subject": "Mathematics",
        "date": "2025-11-20",
        "time": "14:00",
        "duration": 60,
        "status": "upcoming",
        "price": 50,
        "location": "Online",
        "meeting_link": "https://zoom.us/j/123456789"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 15,
      "pages": 1
    }
  }
}
```

#### POST /bookings
Create a new booking.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "tutor_id": 1,
  "subject": "Mathematics",
  "date": "2025-11-20",
  "time": "14:00",
  "duration": 60,
  "location": "Online",
  "notes": "Help with calculus homework"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "booking_id": 1,
    "tutor": {
      "id": 1,
      "name": "Jane Smith"
    },
    "subject": "Mathematics",
    "date": "2025-11-20",
    "time": "14:00",
    "duration": 60,
    "status": "pending",
    "price": 50,
    "location": "Online"
  }
}
```

#### PUT /bookings/{id}/reschedule
Reschedule a booking.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "date": "2025-11-21",
  "time": "15:00",
  "reason": "Schedule conflict"
}
```

#### DELETE /bookings/{id}
Cancel a booking.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

### Payments

#### GET /payments
Get payment history.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "payments": [
      {
        "id": 1,
        "type": "booking",
        "amount": 50,
        "currency": "USD",
        "status": "completed",
        "date": "2025-11-18T10:00:00Z",
        "description": "Booking with Jane Smith",
        "method": "credit_card"
      }
    ]
  }
}
```

#### POST /payments/process
Process a payment.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "amount": 50,
  "currency": "USD",
  "payment_method": "credit_card",
  "booking_id": 1,
  "card_token": "tok_1J2x3..."
}
```

### Reviews

#### GET /reviews
Get reviews for a tutor or course.

**Query Parameters:**
- `tutor_id` (number): Filter by tutor ID
- `course_id` (number): Filter by course ID
- `rating` (number): Filter by rating
- `page` (number): Page number
- `limit` (number): Results per page

**Response:**
```json
{
  "success": true,
  "data": {
    "reviews": [
      {
        "id": 1,
        "reviewer": {
          "id": 2,
          "name": "John Doe"
        },
        "rating": 5,
        "comment": "Excellent tutor! Very patient and knowledgeable.",
        "date": "2025-11-15T10:00:00Z",
        "helpful_count": 12
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 127,
      "pages": 7
    }
  }
}
```

#### POST /reviews
Create a new review.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "tutor_id": 1,
  "rating": 5,
  "comment": "Excellent tutor! Very patient and knowledgeable.",
  "booking_id": 1
}
```

### Certificates

#### GET /certificates
Get user's certificates.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "certificates": [
      {
        "id": 1,
        "title": "Introduction to Calculus",
        "course_name": "Introduction to Calculus",
        "issuer_name": "Jane Smith",
        "completion_date": "2025-11-10",
        "grade": "A",
        "verification_code": "CERT-20251110-ABCD1234",
        "certificate_url": "https://api.tutorpro.com/certificates/1/download",
        "sharing_url": "https://tutorpro.com/share/certificate/ABCD1234"
      }
    ]
  }
}
```

#### GET /certificates/{id}/download
Download certificate PDF.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

#### POST /certificates/{id}/share
Share certificate on social media.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "platform": "LinkedIn",
  "custom_message": "Just completed my calculus course!"
}
```

### YouTube Playlists

#### GET /youtube-playlists
Get YouTube playlists for courses.

**Query Parameters:**
- `course_id` (number): Filter by course ID
- `tutor_id` (number): Filter by tutor ID
- `difficulty` (string): Filter by difficulty level

**Response:**
```json
{
  "success": true,
  "data": {
    "playlists": [
      {
        "id": 1,
        "title": "Calculus Supplementary Videos",
        "description": "Additional videos to help with calculus",
        "course_id": 1,
        "tutor": {
          "id": 1,
          "name": "Jane Smith"
        },
        "video_count": 15,
        "total_duration": 7200,
        "difficulty_level": "beginner",
        "thumbnail_url": "https://img.youtube.com/vi/xxxxxx/maxresdefault.jpg"
      }
    ]
  }
}
```

#### GET /youtube-playlists/{id}/videos
Get videos in a playlist.

**Response:**
```json
{
  "success": true,
  "data": {
    "videos": [
      {
        "id": 1,
        "title": "Introduction to Limits",
        "description": "Understanding the concept of limits",
        "duration": 480,
        "position": 1,
        "thumbnail_url": "https://img.youtube.com/vi/xxxxxx/maxresdefault.jpg",
        "average_rating": 4.5
      }
    ]
  }
}
```

### Q&A System

#### GET /qa/questions
Get questions with filtering and pagination.

**Query Parameters:**
- `page` (number): Page number (default: 1)
- `per_page` (number): Results per page (default: 20)
- `subject_id` (number): Filter by subject ID
- `course_id` (number): Filter by course ID
- `status` (string): Filter by status (Open, Answered, Closed)
- `question_type` (string): Filter by question type
- `difficulty` (string): Filter by difficulty level
- `sort_by` (string): Sort by (latest, popular, unanswered)

**Response:**
```json
{
  "success": true,
  "data": {
    "questions": [
      {
        "id": 1,
        "title": "Help with calculus derivatives",
        "content": "I'm struggling with understanding derivatives...",
        "student": {
          "id": 2,
          "name": "John Doe"
        },
        "subject": {
          "id": 1,
          "name": "Mathematics"
        },
        "question_type": "Concept Clarification",
        "difficulty_level": "Beginner",
        "status": "Open",
        "priority": "Medium",
        "view_count": 15,
        "upvote_count": 3,
        "downvote_count": 0,
        "vote_score": 3,
        "created_at": "2025-11-18T10:00:00Z",
        "time_since_creation": "2 hours ago",
        "answer_count": 2,
        "tags": [
          {
            "id": 1,
            "name": "Calculus",
            "color": "#C0392B"
          }
        ]
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 150,
      "pages": 8
    }
  }
}
```

#### POST /qa/questions
Create a new question.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "title": "Help with calculus derivatives",
  "content": "I'm struggling with understanding derivatives...",
  "subject_id": 1,
  "course_id": 1,
  "question_type": "Concept Clarification",
  "difficulty_level": "Beginner",
  "priority": "Medium",
  "is_public": true,
  "is_anonymous": false,
  "tags": ["Calculus", "Mathematics"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Help with calculus derivatives",
    "content": "I'm struggling with understanding derivatives...",
    "student_id": 2,
    "question_type": "Concept Clarification",
    "difficulty_level": "Beginner",
    "status": "Open",
    "created_at": "2025-11-18T10:00:00Z"
  },
  "message": "Question created successfully"
}
```

#### GET /qa/questions/{id}
Get question details by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Help with calculus derivatives",
    "content": "I'm struggling with understanding derivatives...",
    "student": {
      "id": 2,
      "name": "John Doe"
    },
    "subject": {
      "id": 1,
      "name": "Mathematics"
    },
    "answers": [
      {
        "id": 1,
        "content": "Derivatives measure the rate of change...",
        "tutor": {
          "id": 1,
          "name": "Jane Smith"
        },
        "is_accepted": false,
        "upvote_count": 5,
        "created_at": "2025-11-18T10:30:00Z"
      }
    ]
  }
}
```

#### POST /qa/questions/{id}/answers
Create a new answer for a question.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "content": "Derivatives measure the rate of change..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "content": "Derivatives measure the rate of change...",
    "question_id": 1,
    "tutor_id": 1,
    "is_accepted": false,
    "upvote_count": 0,
    "created_at": "2025-11-18T10:30:00Z"
  },
  "message": "Answer created successfully"
}
```

#### POST /qa/answers/{id}/accept
Accept an answer to a question.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "is_accepted": true,
    "accepted_at": "2025-11-18T11:00:00Z"
  },
  "message": "Answer accepted successfully"
}
```

#### POST /qa/questions/{id}/vote
Vote on a question.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "vote_type": "Upvote"
}
```

#### POST /qa/answers/{id}/vote
Vote on an answer.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "vote_type": "Upvote"
}
```

#### POST /qa/questions/{id}/follow
Follow a question for notifications.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Request Body:**
```json
{
  "notification_enabled": true
}
```

#### GET /qa/tags
Get popular Q&A tags.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Mathematics",
      "description": "Questions related to mathematics topics",
      "color": "#3498DB",
      "icon": "fa-calculator",
      "question_count": 45
    }
  ]
}
```

### Notifications

#### GET /notifications
Get user notifications.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

**Query Parameters:**
- `type` (string): Filter by notification type
- `read` (boolean): Filter by read status
- `page` (number): Page number
- `limit` (number): Results per page

**Response:**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": 1,
        "type": "booking_reminder",
        "title": "Booking Reminder",
        "message": "You have a session with Jane Smith tomorrow at 2:00 PM",
        "read": false,
        "created_at": "2025-11-17T10:00:00Z"
      }
    ],
    "unread_count": 3
  }
}
```

#### PUT /notifications/{id}/read
Mark notification as read.

**Headers:**
```
Authorization: Bearer <your-jwt-token>
```

## Error Codes

| Code | Description |
|------|-------------|
| AUTH_001 | Invalid authentication token |
| AUTH_002 | Token expired |
| AUTH_003 | Insufficient permissions |
| VALIDATION_001 | Invalid input data |
| VALIDATION_002 | Missing required field |
| RESOURCE_001 | Resource not found |
| RESOURCE_002 | Resource already exists |
| BOOKING_001 | Booking slot unavailable |
| BOOKING_002 | Booking cancellation deadline passed |
| PAYMENT_001 | Payment failed |
| PAYMENT_002 | Insufficient funds |
| RATE_LIMIT_001 | Rate limit exceeded |
| SERVER_001 | Internal server error |

## SDKs and Libraries

We provide official SDKs for the following platforms:

- [Python SDK](https://github.com/tutorpro/python-sdk)
- [JavaScript SDK](https://github.com/tutorpro/javascript-sdk)
- [iOS SDK](https://github.com/tutorpro/ios-sdk)
- [Android SDK](https://github.com/tutorpro/android-sdk)

## Support

For API support and questions:

- Email: api-support@tutorpro.com
- Documentation: https://docs.tutorpro.com
- Status Page: https://status.tutorpro.com

## Changelog

### v1.3.0 (2025-11-18)
- Added comprehensive Q&A system
- Implemented question and answer management
- Added voting and following functionality
- Enhanced tag-based categorization

### v1.2.0 (2025-11-18)
- Added certificate sharing endpoints
- Added YouTube playlist integration
- Enhanced review sharing with social media

### v1.1.0 (2025-11-01)
- Added advanced search filters
- Implemented booking rescheduling
- Added payment history endpoints

### v1.0.0 (2025-10-01)
- Initial API release
- Core authentication and user management
- Tutor and course endpoints
- Booking and payment functionality