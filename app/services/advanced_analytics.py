"""
Advanced Analytics Service for TutorPro
Provides predictive analytics, business intelligence, and advanced reporting capabilities
"""

from datetime import datetime, timedelta, date
from sqlalchemy import func, extract, and_, or_, desc
from flask import current_app
from app import db
from app.models.payment import Payment
from app.models.booking import Booking
from app.models.user import User
from app.models.tutor import TutorProfile
from app.models.course import Course, CourseEnrollment
from app.models.verification import TutorReview as Review
import logging
import json

logger = logging.getLogger(__name__)

class AdvancedAnalytics:
    """Advanced analytics service with predictive capabilities and business intelligence"""
    
    def __init__(self):
        self.prediction_models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize prediction models"""
        self.prediction_models = {
            'revenue_forecast': RevenueForecastModel(),
            'user_churn': UserChurnModel(),
            'tutor_performance': TutorPerformanceModel(),
            'course_completion': CourseCompletionModel()
        }
    
    def get_business_intelligence_dashboard(self, start_date=None, end_date=None):
        """Generate comprehensive business intelligence dashboard"""
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Revenue Intelligence
            revenue_intel = self._get_revenue_intelligence(start_date, end_date)
            
            # User Intelligence
            user_intel = self._get_user_intelligence(start_date, end_date)
            
            # Market Intelligence
            market_intel = self._get_market_intelligence(start_date, end_date)
            
            # Operational Intelligence
            operational_intel = self._get_operational_intelligence(start_date, end_date)
            
            # Predictive Insights
            predictive_insights = self._get_predictive_insights()
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'revenue_intelligence': revenue_intel,
                'user_intelligence': user_intel,
                'market_intelligence': market_intel,
                'operational_intelligence': operational_intel,
                'predictive_insights': predictive_insights,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate BI dashboard: {str(e)}")
            return self._get_empty_bi_dashboard()
    
    def _get_revenue_intelligence(self, start_date, end_date):
        """Generate revenue intelligence"""
        try:
            # Revenue trends
            revenue_trends = self._analyze_revenue_trends(start_date, end_date)
            
            # Revenue forecasting
            forecast = self.prediction_models['revenue_forecast'].predict(
                start_date, end_date, days_ahead=30
            )
            
            # Revenue by segment
            segment_revenue = self._get_revenue_by_segment(start_date, end_date)
            
            # Revenue concentration analysis
            concentration = self._analyze_revenue_concentration(start_date, end_date)
            
            return {
                'trends': revenue_trends,
                'forecast': forecast,
                'segment_analysis': segment_revenue,
                'concentration_analysis': concentration
            }
            
        except Exception as e:
            logger.error(f"Failed to get revenue intelligence: {str(e)}")
            return {}
    
    def _get_user_intelligence(self, start_date, end_date):
        """Generate user intelligence"""
        try:
            # User acquisition analysis
            acquisition = self._analyze_user_acquisition(start_date, end_date)
            
            # User engagement metrics
            engagement = self._analyze_user_engagement(start_date, end_date)
            
            # User retention analysis
            retention = self._analyze_user_retention(start_date, end_date)
            
            # User lifetime value
            ltv_analysis = self._calculate_customer_lifetime_value()
            
            # Churn prediction
            churn_risk = self.prediction_models['user_churn'].predict_churn_risk()
            
            return {
                'acquisition': acquisition,
                'engagement': engagement,
                'retention': retention,
                'lifetime_value': ltv_analysis,
                'churn_prediction': churn_risk
            }
            
        except Exception as e:
            logger.error(f"Failed to get user intelligence: {str(e)}")
            return {}
    
    def _get_market_intelligence(self, start_date, end_date):
        """Generate market intelligence"""
        try:
            # Subject demand analysis
            subject_demand = self._analyze_subject_demand(start_date, end_date)
            
            # Geographic analysis
            geographic = self._analyze_geographic_distribution(start_date, end_date)
            
            # Price elasticity analysis
            price_elasticity = self._analyze_price_elasticity(start_date, end_date)
            
            # Competitor insights (simulated)
            competitor_insights = self._generate_competitor_insights()
            
            return {
                'subject_demand': subject_demand,
                'geographic_distribution': geographic,
                'price_elasticity': price_elasticity,
                'competitor_insights': competitor_insights
            }
            
        except Exception as e:
            logger.error(f"Failed to get market intelligence: {str(e)}")
            return {}
    
    def _get_operational_intelligence(self, start_date, end_date):
        """Generate operational intelligence"""
        try:
            # Tutor performance analysis
            tutor_performance = self.prediction_models['tutor_performance'].analyze_performance()
            
            # Booking efficiency
            booking_efficiency = self._analyze_booking_efficiency(start_date, end_date)
            
            # Platform utilization
            utilization = self._analyze_platform_utilization(start_date, end_date)
            
            # Quality metrics
            quality_metrics = self._analyze_quality_metrics(start_date, end_date)
            
            return {
                'tutor_performance': tutor_performance,
                'booking_efficiency': booking_efficiency,
                'platform_utilization': utilization,
                'quality_metrics': quality_metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to get operational intelligence: {str(e)}")
            return {}
    
    def _get_predictive_insights(self):
        """Generate predictive insights"""
        try:
            insights = []
            
            # Revenue growth prediction
            revenue_growth = self.prediction_models['revenue_forecast'].predict_growth_rate()
            if revenue_growth > 0:
                insights.append({
                    'type': 'revenue_growth',
                    'confidence': revenue_growth['confidence'],
                    'prediction': revenue_growth['prediction'],
                    'impact': 'high',
                    'recommendation': 'Scale up marketing efforts to capture growth momentum'
                })
            
            # High-risk users
            churn_risk = self.prediction_models['user_churn'].identify_high_risk_users()
            if churn_risk:
                insights.append({
                    'type': 'churn_risk',
                    'affected_users': len(churn_risk),
                    'confidence': 0.75,
                    'impact': 'high',
                    'recommendation': 'Implement retention campaigns for at-risk users'
                })
            
            # Underperforming tutors
            underperforming = self.prediction_models['tutor_performance'].identify_underperforming()
            if underperforming:
                insights.append({
                    'type': 'tutor_performance',
                    'affected_tutors': len(underperforming),
                    'confidence': 0.80,
                    'impact': 'medium',
                    'recommendation': 'Provide training and support for underperforming tutors'
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get predictive insights: {str(e)}")
            return []
    
    def _analyze_revenue_trends(self, start_date, end_date):
        """Analyze revenue trends"""
        try:
            # Daily revenue data
            daily_revenue = db.session.query(
                func.date(Payment.processed_at).label('date'),
                func.sum(Payment.amount).label('revenue')
            ).filter(
                Payment.status == 'Completed',
                Payment.processed_at >= start_date,
                Payment.processed_at <= end_date
            ).group_by(
                func.date(Payment.processed_at)
            ).order_by('date').all()
            
            # Calculate trend metrics
            revenue_data = [(date.isoformat(), float(revenue or 0)) for date, revenue in daily_revenue]
            
            if len(revenue_data) < 2:
                return {'trend': 'insufficient_data', 'growth_rate': 0}
            
            # Simple linear regression for trend
            x_values = list(range(len(revenue_data)))
            y_values = [revenue for _, revenue in revenue_data]
            
            trend_slope = self._calculate_trend_slope(x_values, y_values)
            
            # Determine trend direction
            if trend_slope > 0.1:
                trend_direction = 'increasing'
            elif trend_slope < -0.1:
                trend_direction = 'decreasing'
            else:
                trend_direction = 'stable'
            
            return {
                'trend': trend_direction,
                'slope': trend_slope,
                'data': revenue_data,
                'growth_rate': (trend_slope / (sum(y_values) / len(y_values))) * 100 if y_values else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze revenue trends: {str(e)}")
            return {'trend': 'error', 'growth_rate': 0}
    
    def _analyze_user_acquisition(self, start_date, end_date):
        """Analyze user acquisition patterns"""
        try:
            # New users by date
            new_users = db.session.query(
                func.date(User.created_at).label('date'),
                func.count(User.id).label('new_users')
            ).filter(
                User.created_at >= start_date,
                User.created_at <= end_date
            ).group_by(
                func.date(User.created_at)
            ).order_by('date').all()
            
            # Users by source (if available)
            # This would require tracking source in user registration
            
            # Users by role
            users_by_role = db.session.query(
                User.role,
                func.count(User.id).label('count')
            ).filter(
                User.created_at >= start_date,
                User.created_at <= end_date
            ).group_by(User.role).all()
            
            return {
                'daily_acquisition': [(date.isoformat(), count) for date, count in new_users],
                'by_role': {role: count for role, count in users_by_role},
                'total_new_users': sum(count for _, count in new_users)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze user acquisition: {str(e)}")
            return {}
    
    def _analyze_user_engagement(self, start_date, end_date):
        """Analyze user engagement metrics"""
        try:
            # Active users (users with bookings)
            active_users = db.session.query(
                func.count(func.distinct(Booking.student_id))
            ).filter(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date
            ).scalar() or 0
            
            # Total users
            total_users = db.session.query(func.count(User.id)).scalar() or 0
            
            # Booking frequency
            booking_frequency = db.session.query(
                func.count(Booking.id).label('total_bookings'),
                func.count(func.distinct(Booking.student_id)).label('unique_students')
            ).filter(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date
            ).first()
            
            engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
            avg_bookings_per_user = (booking_frequency.total_bookings / booking_frequency.unique_students) if booking_frequency.unique_students > 0 else 0
            
            return {
                'active_users': active_users,
                'total_users': total_users,
                'engagement_rate': engagement_rate,
                'avg_bookings_per_user': avg_bookings_per_user,
                'total_bookings': booking_frequency.total_bookings or 0
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze user engagement: {str(e)}")
            return {}
    
    def _analyze_user_retention(self, start_date, end_date):
        """Analyze user retention metrics"""
        try:
            # Cohort analysis - users who joined in the period
            cohort_users = db.session.query(User.id).filter(
                User.created_at >= start_date,
                User.created_at <= end_date
            ).subquery()
            
            # Retained users (users who booked after initial period)
            retained_users = db.session.query(
                func.count(func.distinct(Booking.student_id))
            ).filter(
                Booking.student_id.in_(cohort_users),
                Booking.created_at > end_date
            ).scalar() or 0
            
            total_cohort_users = db.session.query(func.count(User.id)).filter(
                User.created_at >= start_date,
                User.created_at <= end_date
            ).scalar() or 0
            
            retention_rate = (retained_users / total_cohort_users * 100) if total_cohort_users > 0 else 0
            
            return {
                'cohort_size': total_cohort_users,
                'retained_users': retained_users,
                'retention_rate': retention_rate
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze user retention: {str(e)}")
            return {}
    
    def _calculate_customer_lifetime_value(self):
        """Calculate customer lifetime value"""
        try:
            # Average revenue per user
            avg_revenue_per_user = db.session.query(
                func.avg(Payment.amount)
            ).filter(
                Payment.status == 'Completed'
            ).scalar() or 0
            
            # Average user lifetime (simplified - time between first and last booking)
            user_lifetimes = db.session.query(
                Booking.student_id,
                func.min(Booking.created_at).label('first_booking'),
                func.max(Booking.created_at).label('last_booking')
            ).group_by(Booking.student_id).all()
            
            if not user_lifetimes:
                return {'average_ltv': 0, 'total_ltv': 0}
            
            total_days = sum([(last - first).days for _, first, last in user_lifetimes if last and first])
            avg_lifetime_days = total_days / len(user_lifetimes)
            
            # Simplified LTV calculation
            avg_bookings_per_user = db.session.query(
                func.count(Booking.id) / func.count(func.distinct(Booking.student_id))
            ).scalar() or 0
            
            average_ltv = avg_revenue_per_user * avg_bookings_per_user
            total_ltv = average_ltv * len(user_lifetimes)
            
            return {
                'average_ltv': average_ltv,
                'total_ltv': total_ltv,
                'avg_customer_lifetime_days': avg_lifetime_days,
                'avg_revenue_per_booking': avg_revenue_per_user
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate customer lifetime value: {str(e)}")
            return {'average_ltv': 0, 'total_ltv': 0}
    
    def _analyze_subject_demand(self, start_date, end_date):
        """Analyze subject demand trends"""
        try:
            # This would require subject information in bookings or courses
            # For now, return a placeholder structure
            return {
                'top_subjects': [
                    {'subject': 'Mathematics', 'demand_score': 85, 'growth_rate': 12},
                    {'subject': 'English', 'demand_score': 78, 'growth_rate': 8},
                    {'subject': 'Science', 'demand_score': 72, 'growth_rate': 15},
                    {'subject': 'Programming', 'demand_score': 68, 'growth_rate': 25}
                ],
                'emerging_subjects': [
                    {'subject': 'Data Science', 'demand_score': 45, 'growth_rate': 40},
                    {'subject': 'Machine Learning', 'demand_score': 38, 'growth_rate': 35}
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze subject demand: {str(e)}")
            return {}
    
    def _analyze_geographic_distribution(self, start_date, end_date):
        """Analyze geographic distribution of users"""
        try:
            # This would require location data in user profiles
            # For now, return a placeholder structure
            return {
                'top_regions': [
                    {'region': 'North America', 'user_percentage': 45, 'growth_rate': 10},
                    {'region': 'Europe', 'user_percentage': 30, 'growth_rate': 8},
                    {'region': 'Asia', 'user_percentage': 20, 'growth_rate': 25},
                    {'region': 'Other', 'user_percentage': 5, 'growth_rate': 5}
                ],
                'emerging_markets': [
                    {'region': 'Southeast Asia', 'potential': 'high', 'current_penetration': 8},
                    {'region': 'Latin America', 'potential': 'medium', 'current_penetration': 5}
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze geographic distribution: {str(e)}")
            return {}
    
    def _analyze_price_elasticity(self, start_date, end_date):
        """Analyze price elasticity of demand"""
        try:
            # This would require price variation data
            # For now, return a placeholder structure
            return {
                'elasticity_coefficient': -1.2,
                'optimal_price_range': {
                    'min': 25,
                    'max': 75,
                    'recommended': 45
                },
                'price_sensitivity': 'medium'
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze price elasticity: {str(e)}")
            return {}
    
    def _generate_competitor_insights(self):
        """Generate simulated competitor insights"""
        try:
            return {
                'market_share': {
                    'tutorpro': 15,
                    'competitor_a': 35,
                    'competitor_b': 25,
                    'others': 25
                },
                'competitive_advantages': [
                    'Better user interface',
                    'Comprehensive analytics',
                    'Advanced matching algorithm'
                ],
                'competitive_gaps': [
                    'Mobile app availability',
                    'International presence',
                    'Enterprise features'
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to generate competitor insights: {str(e)}")
            return {}
    
    def _analyze_booking_efficiency(self, start_date, end_date):
        """Analyze booking efficiency metrics"""
        try:
            # Booking completion rate
            total_bookings = db.session.query(func.count(Booking.id)).filter(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date
            ).scalar() or 0
            
            completed_bookings = db.session.query(func.count(Booking.id)).filter(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date,
                Booking.status == 'completed'
            ).scalar() or 0
            
            completion_rate = (completed_bookings / total_bookings * 100) if total_bookings > 0 else 0
            
            # Cancellation analysis
            cancelled_bookings = db.session.query(func.count(Booking.id)).filter(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date,
                Booking.status == 'cancelled'
            ).scalar() or 0
            
            cancellation_rate = (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0
            
            return {
                'total_bookings': total_bookings,
                'completed_bookings': completed_bookings,
                'cancelled_bookings': cancelled_bookings,
                'completion_rate': completion_rate,
                'cancellation_rate': cancellation_rate
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze booking efficiency: {str(e)}")
            return {}
    
    def _analyze_platform_utilization(self, start_date, end_date):
        """Analyze platform utilization metrics"""
        try:
            # Tutor utilization
            active_tutors = db.session.query(
                func.count(func.distinct(Booking.tutor_id))
            ).filter(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date
            ).scalar() or 0
            
            total_tutors = db.session.query(func.count(TutorProfile.id)).scalar() or 0
            tutor_utilization = (active_tutors / total_tutors * 100) if total_tutors > 0 else 0
            
            # Course utilization
            active_courses = db.session.query(
                func.count(func.distinct(CourseEnrollment.course_id))
            ).filter(
                CourseEnrollment.enrolled_at >= start_date,
                CourseEnrollment.enrolled_at <= end_date
            ).scalar() or 0
            
            total_courses = db.session.query(func.count(Course.id)).scalar() or 0
            course_utilization = (active_courses / total_courses * 100) if total_courses > 0 else 0
            
            return {
                'tutor_utilization': {
                    'active_tutors': active_tutors,
                    'total_tutors': total_tutors,
                    'utilization_rate': tutor_utilization
                },
                'course_utilization': {
                    'active_courses': active_courses,
                    'total_courses': total_courses,
                    'utilization_rate': course_utilization
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze platform utilization: {str(e)}")
            return {}
    
    def _analyze_quality_metrics(self, start_date, end_date):
        """Analyze quality metrics"""
        try:
            # Average ratings
            avg_rating = db.session.query(
                func.avg(Review.rating)
            ).filter(
                Review.created_at >= start_date,
                Review.created_at <= end_date
            ).scalar() or 0
            
            # Review distribution
            review_distribution = db.session.query(
                Review.rating,
                func.count(Review.id).label('count')
            ).filter(
                Review.created_at >= start_date,
                Review.created_at <= end_date
            ).group_by(Review.rating).all()
            
            # Complaint rate (simplified - negative reviews)
            negative_reviews = db.session.query(func.count(Review.id)).filter(
                Review.created_at >= start_date,
                Review.created_at <= end_date,
                Review.rating <= 2
            ).scalar() or 0
            
            total_reviews = db.session.query(func.count(Review.id)).filter(
                Review.created_at >= start_date,
                Review.created_at <= end_date
            ).scalar() or 0
            
            complaint_rate = (negative_reviews / total_reviews * 100) if total_reviews > 0 else 0
            
            return {
                'average_rating': float(avg_rating),
                'review_distribution': {rating: count for rating, count in review_distribution},
                'complaint_rate': complaint_rate,
                'total_reviews': total_reviews
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze quality metrics: {str(e)}")
            return {}
    
    def _get_revenue_by_segment(self, start_date, end_date):
        """Get revenue breakdown by segment"""
        try:
            # Revenue by user type
            user_segment_revenue = db.session.query(
                User.role,
                func.sum(Payment.amount).label('revenue'),
                func.count(Payment.id).label('transactions')
            ).join(Booking).join(User).filter(
                Payment.status == 'Completed',
                Payment.processed_at >= start_date,
                Payment.processed_at <= end_date
            ).group_by(User.role).all()
            
            # Revenue by payment method
            payment_method_revenue = db.session.query(
                Payment.payment_gateway,
                func.sum(Payment.amount).label('revenue'),
                func.count(Payment.id).label('transactions')
            ).filter(
                Payment.status == 'Completed',
                Payment.processed_at >= start_date,
                Payment.processed_at <= end_date
            ).group_by(Payment.payment_gateway).all()
            
            return {
                'by_user_type': {
                    role: {'revenue': float(revenue or 0), 'transactions': transactions}
                    for role, revenue, transactions in user_segment_revenue
                },
                'by_payment_method': {
                    method: {'revenue': float(revenue or 0), 'transactions': transactions}
                    for method, revenue, transactions in payment_method_revenue
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get revenue by segment: {str(e)}")
            return {}
    
    def _analyze_revenue_concentration(self, start_date, end_date):
        """Analyze revenue concentration (Pareto analysis)"""
        try:
            # Top revenue contributors
            top_contributors = db.session.query(
                User.id,
                User.first_name,
                User.last_name,
                func.sum(Payment.amount).label('total_revenue')
            ).join(Booking).join(User).filter(
                Payment.status == 'Completed',
                Payment.processed_at >= start_date,
                Payment.processed_at <= end_date
            ).group_by(
                User.id, User.first_name, User.last_name
            ).order_by(desc('total_revenue')).limit(10).all()
            
            total_revenue = sum(contributor.total_revenue or 0 for contributor in top_contributors)
            
            # Calculate concentration metrics
            top_10_percent_revenue = (total_revenue / self._get_total_revenue(start_date, end_date) * 100) if self._get_total_revenue(start_date, end_date) > 0 else 0
            
            return {
                'top_contributors': [
                    {
                        'user_id': contributor.id,
                        'name': f"{contributor.first_name} {contributor.last_name}",
                        'revenue': float(contributor.total_revenue or 0)
                    }
                    for contributor in top_contributors
                ],
                'concentration_metrics': {
                    'top_10_percent_contribution': top_10_percent_revenue,
                    'total_top_10_revenue': float(total_revenue)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze revenue concentration: {str(e)}")
            return {}
    
    def _get_total_revenue(self, start_date, end_date):
        """Get total revenue for period"""
        try:
            return db.session.query(func.sum(Payment.amount)).filter(
                Payment.status == 'Completed',
                Payment.processed_at >= start_date,
                Payment.processed_at <= end_date
            ).scalar() or 0
            
        except Exception as e:
            logger.error(f"Failed to get total revenue: {str(e)}")
            return 0
    
    def _calculate_trend_slope(self, x_values, y_values):
        """Calculate simple linear regression slope"""
        try:
            if len(x_values) != len(y_values) or len(x_values) < 2:
                return 0
            
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            return slope
            
        except Exception as e:
            logger.error(f"Failed to calculate trend slope: {str(e)}")
            return 0
    
    def _get_empty_bi_dashboard(self):
        """Return empty BI dashboard structure"""
        return {
            'period': {
                'start_date': None,
                'end_date': None
            },
            'revenue_intelligence': {},
            'user_intelligence': {},
            'market_intelligence': {},
            'operational_intelligence': {},
            'predictive_insights': [],
            'generated_at': datetime.utcnow().isoformat(),
            'error': 'Failed to generate dashboard'
        }


class RevenueForecastModel:
    """Simple revenue forecasting model"""
    
    def predict(self, start_date, end_date, days_ahead=30):
        """Predict revenue for next N days"""
        try:
            # Get historical data
            historical_data = db.session.query(
                func.date(Payment.processed_at).label('date'),
                func.sum(Payment.amount).label('revenue')
            ).filter(
                Payment.status == 'Completed',
                Payment.processed_at >= start_date - timedelta(days=60),
                Payment.processed_at <= end_date
            ).group_by(
                func.date(Payment.processed_at)
            ).order_by('date').all()
            
            if len(historical_data) < 7:
                return {'forecast': [], 'confidence': 0}
            
            # Simple moving average forecast
            revenues = [float(revenue or 0) for _, revenue in historical_data]
            recent_avg = sum(revenues[-7:]) / 7
            
            # Generate forecast
            forecast = []
            for i in range(days_ahead):
                forecast_date = end_date + timedelta(days=i+1)
                # Add some randomness and trend
                forecast_revenue = recent_avg * (1 + (i * 0.01)) + (i % 3 - 1) * recent_avg * 0.05
                forecast.append({
                    'date': forecast_date.strftime('%Y-%m-%d'),
                    'predicted_revenue': max(0, forecast_revenue)
                })
            
            return {
                'forecast': forecast,
                'confidence': 0.75,  # Simplified confidence
                'method': 'moving_average_with_trend'
            }
            
        except Exception as e:
            logger.error(f"Failed to predict revenue: {str(e)}")
            return {'forecast': [], 'confidence': 0}
    
    def predict_growth_rate(self):
        """Predict revenue growth rate"""
        try:
            # Get last 30 days vs previous 30 days
            end_date = datetime.utcnow()
            current_period_start = end_date - timedelta(days=30)
            previous_period_start = end_date - timedelta(days=60)
            
            current_revenue = db.session.query(func.sum(Payment.amount)).filter(
                Payment.status == 'Completed',
                Payment.processed_at >= current_period_start,
                Payment.processed_at <= end_date
            ).scalar() or 0
            
            previous_revenue = db.session.query(func.sum(Payment.amount)).filter(
                Payment.status == 'Completed',
                Payment.processed_at >= previous_period_start,
                Payment.processed_at < current_period_start
            ).scalar() or 0
            
            if previous_revenue == 0:
                return {'prediction': 0, 'confidence': 0}
            
            growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100
            
            return {
                'prediction': growth_rate,
                'confidence': 0.70,
                'current_period_revenue': float(current_revenue),
                'previous_period_revenue': float(previous_revenue)
            }
            
        except Exception as e:
            logger.error(f"Failed to predict growth rate: {str(e)}")
            return {'prediction': 0, 'confidence': 0}


class UserChurnModel:
    """Simple user churn prediction model"""
    
    def predict_churn_risk(self):
        """Predict churn risk for users"""
        try:
            # Get users with no recent activity
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            at_risk_users = db.session.query(User).filter(
                User.created_at < cutoff_date,
                ~User.id.in_(
                    db.session.query(Booking.student_id).filter(
                        Booking.created_at >= cutoff_date
                    )
                )
            ).limit(100).all()
            
            risk_scores = []
            for user in at_risk_users:
                # Simple risk scoring based on last activity
                risk_score = min(0.9, (datetime.utcnow() - user.created_at).days / 365)
                risk_scores.append({
                    'user_id': user.id,
                    'email': user.email,
                    'risk_score': risk_score,
                    'risk_level': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.4 else 'low'
                })
            
            return risk_scores
            
        except Exception as e:
            logger.error(f"Failed to predict churn risk: {str(e)}")
            return []
    
    def identify_high_risk_users(self):
        """Identify users at high risk of churn"""
        risk_scores = self.predict_churn_risk()
        return [user for user in risk_scores if user['risk_level'] == 'high']


class TutorPerformanceModel:
    """Tutor performance analysis model"""
    
    def analyze_performance(self):
        """Analyze tutor performance metrics"""
        try:
            # Get tutor performance data
            tutor_performance = db.session.query(
                TutorProfile.id,
                TutorProfile.title,
                User.first_name,
                User.last_name,
                func.count(Booking.id).label('total_bookings'),
                func.count(func.distinct(Booking.student_id)).label('unique_students'),
                func.avg(Review.rating).label('average_rating'),
                func.sum(Payment.amount).label('total_revenue')
            ).join(Booking).join(User).join(Payment, Booking.id == Payment.booking_id).join(
                Review, Booking.tutor_id == Review.tutor_id, isouter=True
            ).filter(
                Payment.status == 'Completed'
            ).group_by(
                TutorProfile.id, TutorProfile.title, User.first_name, User.last_name
            ).all()
            
            performance_data = []
            for tutor in tutor_performance:
                # Calculate performance score
                booking_score = min(100, tutor.total_bookings / 10 * 100)
                rating_score = (tutor.average_rating or 0) * 20
                revenue_score = min(100, (tutor.total_revenue or 0) / 1000 * 100)
                
                overall_score = (booking_score + rating_score + revenue_score) / 3
                
                performance_data.append({
                    'tutor_id': tutor.id,
                    'name': f"{tutor.first_name} {tutor.last_name}",
                    'title': tutor.title,
                    'total_bookings': tutor.total_bookings,
                    'unique_students': tutor.unique_students,
                    'average_rating': float(tutor.average_rating or 0),
                    'total_revenue': float(tutor.total_revenue or 0),
                    'performance_score': overall_score,
                    'performance_level': 'excellent' if overall_score > 80 else 'good' if overall_score > 60 else 'needs_improvement'
                })
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to analyze tutor performance: {str(e)}")
            return []
    
    def identify_underperforming(self):
        """Identify underperforming tutors"""
        performance_data = self.analyze_performance()
        return [tutor for tutor in performance_data if tutor['performance_level'] == 'needs_improvement']


class CourseCompletionModel:
    """Course completion prediction model"""
    
    def predict_completion_rates(self):
        """Predict course completion rates"""
        try:
            # Get course completion data
            course_data = db.session.query(
                Course.id,
                Course.title,
                func.count(CourseEnrollment.id).label('total_enrollments'),
                func.count(func.distinct(CourseEnrollment.id)).filter(
                    CourseEnrollment.status == 'completed'
                ).label('completed_enrollments')
            ).outerjoin(CourseEnrollment).group_by(
                Course.id, Course.title
            ).all()
            
            completion_predictions = []
            for course in course_data:
                completion_rate = (course.completed_enrollments / course.total_enrollments * 100) if course.total_enrollments > 0 else 0
                
                completion_predictions.append({
                    'course_id': course.id,
                    'title': course.title,
                    'total_enrollments': course.total_enrollments,
                    'completed_enrollments': course.completed_enrollments,
                    'completion_rate': completion_rate,
                    'predicted_completion': completion_rate,  # Simplified - uses historical rate
                    'confidence': 0.75
                })
            
            return completion_predictions
            
        except Exception as e:
            logger.error(f"Failed to predict completion rates: {str(e)}")
            return []