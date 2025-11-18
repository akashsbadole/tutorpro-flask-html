from app.models.user import User, UserProfile, LearnerProfile
from app.models.tutor import TutorProfile
from app.models.course import (Subject, Course, CourseSyllabus, TutorSubject, SyllabusTopic,
                              CourseMaterial, CourseEnrollment, Assignment, AssignmentSubmission,
                              AssignmentRubric, RubricCriteria, RubricScore, StudentProgress,
                              DiscussionBoard, DiscussionPost, Quiz, QuizQuestion, QuizOption,
                              QuizAttempt, QuizAnswer, Achievement, EarnedAchievement)
from app.models.booking import Booking, TutorAvailability, MeetingLink, DemoRequest
from app.models.payment import Payment, PaymentMethod, Transaction, Payout
from app.models.review import Review, Rating, TutorRatingSummary
from app.models.job import JobPost, JobApplication, JobApplicationNote, JobSaved, JobView
from app.models.notification import Notification, EmailLog, NotificationPreference, NotificationTemplate
from app.models.meeting import (Meeting, MeetingParticipant, MeetingRecording, MeetingTemplate,
                               MeetingCalendar, MeetingReminder, MeetingAnalytics)
from app.models.demo import (DemoClass, DemoFeedback, DemoMaterial, DemoFollowUp,
                           DemoTemplate, DemoAnalytics, DemoRequest as NewDemoRequest)

# This file imports all models to ensure they're registered with SQLAlchemy
# when the application is created.