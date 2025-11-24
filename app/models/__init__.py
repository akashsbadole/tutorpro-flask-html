from app.models.user import User, UserProfile
from app.models.student import LearnerProfile
from app.models.tutor import TutorProfile, TutorSubject, TutorCertification, TutorAvailability
from app.models.category import SubjectCategory, Subject, LearningObjective, SubjectLevel
from app.models.verification import VerificationDocument, TutorReview, TutorRating
from app.models.booking import Booking, BookingSession, GroupSession, AvailabilityConflict
from app.models.payment import Payment, PaymentMethod, Payout, Refund, Transaction

# Legacy models (to be reviewed for deprecation or integration)
from app.models.course import (Course, CourseSyllabus, CourseTopic,
                              CourseMaterial, CourseEnrollment, CourseAssignment,
                              CourseDiscussion, CourseQuiz, CourseProgress,
                              CourseAnnouncement, CourseAchievement, StudentAchievement)
# Legacy booking models - these may need to be created or imported from correct locations
# from app.models.booking import TutorAvailability as LegacyTutorAvailability, MeetingLink, DemoRequest as BookingDemoRequest
from app.models.payment import Payment as LegacyPayment, PaymentMethod as LegacyPaymentMethod, Transaction as LegacyTransaction, Payout as LegacyPayout
# Import review models - using only the verification.py Review model to avoid conflicts
# from app.models.review import Review as StudentReview, Rating, TutorRatingSummary
# from app.models.review import Rating, TutorRatingSummary  # Commented out to avoid table name conflict
# from app.models.review import Rating, TutorRatingSummary
from app.models.job import JobPost, JobApplication, JobApplicationNote, JobSaved, JobView
from app.models.notification import Notification, EmailLog, NotificationTemplate
from app.models.meeting import (Meeting, MeetingParticipant, MeetingRecording, MeetingTemplate,
                               MeetingCalendar, MeetingReminder, MeetingAnalytics)
from app.models.demo import (DemoSession, DemoFeedback, DemoAvailability, DemoTemplate,
                           DemoAnalytics)
# DemoRequestFeedback model doesn't exist in booking.py
# from app.models.booking import DemoRequestFeedback

# New marketplace models
from app.models.certificate import Certificate, CertificateTemplate, CertificateSharing
from app.models.youtube_playlist import YouTubePlaylist, YouTubeVideo, VideoComment, VideoRating
from app.models.review_sharing import ReviewSharing, SocialMediaPost
from app.models.email_notification import EmailNotification, EmailTemplate, EmailNotificationPreference as NotificationPreference
from app.models.api_documentation import APIDocumentation, APIExample, APITestCase, APIChangeLog
from app.models.qa_system import Question, Answer, Tag, QuestionTag, QuestionVote, AnswerVote, QuestionFollow

# Enterprise models
from app.models.enterprise import (Organization, Department, OrganizationUser, TrainingProgram,
                             TrainingEnrollment, BillingInvoice, BulkOperation)

# This file imports all models to ensure they're registered with SQLAlchemy
# when the application is created.