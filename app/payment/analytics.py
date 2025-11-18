from datetime import datetime, timedelta
from sqlalchemy import func, extract
from flask import current_app
from app import db
from app.models.payment import Payment, Transaction, Payout
from app.models.booking import Booking
from app.models.user import User
from app.models.tutor import TutorProfile
import logging

logger = logging.getLogger(__name__)

class PaymentAnalytics:
    """Service for payment analytics and reporting"""
    
    def get_revenue_summary(self, start_date=None, end_date=None, currency=None):
        """Get revenue summary for a given period"""
        try:
            query = db.session.query(
                func.sum(Payment.amount).label('total_revenue'),
                func.count(Payment.id).label('total_transactions'),
                func.avg(Payment.amount).label('average_transaction_value')
            ).filter(Payment.status == 'Completed')
            
            # Apply date filters
            if start_date:
                query = query.filter(Payment.processed_at >= start_date)
            if end_date:
                query = query.filter(Payment.processed_at <= end_date)
            
            # Apply currency filter
            if currency:
                query = query.filter(Payment.currency == currency)
            
            result = query.first()
            
            return {
                'total_revenue': float(result.total_revenue or 0),
                'total_transactions': result.total_transactions or 0,
                'average_transaction_value': float(result.average_transaction_value or 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get revenue summary: {str(e)}")
            return {
                'total_revenue': 0,
                'total_transactions': 0,
                'average_transaction_value': 0
            }
    
    def get_payment_method_analytics(self, start_date=None, end_date=None):
        """Get analytics by payment method"""
        try:
            query = db.session.query(
                PaymentMethod.payment_type,
                func.count(Payment.id).label('transaction_count'),
                func.sum(Payment.amount).label('total_amount'),
                func.avg(Payment.amount).label('average_amount')
            ).join(PaymentMethod).filter(
                Payment.status == 'Completed'
            )
            
            # Apply date filters
            if start_date:
                query = query.filter(Payment.processed_at >= start_date)
            if end_date:
                query = query.filter(Payment.processed_at <= end_date)
            
            results = query.group_by(PaymentMethod.payment_type).all()
            
            analytics = {}
            for payment_type, count, total_amount, avg_amount in results:
                analytics[payment_type] = {
                    'transaction_count': count,
                    'total_amount': float(total_amount or 0),
                    'average_amount': float(avg_amount or 0)
                }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get payment method analytics: {str(e)}")
            return {}
    
    def get_monthly_revenue(self, year=None):
        """Get monthly revenue for a given year"""
        try:
            if not year:
                year = datetime.now().year
            
            query = db.session.query(
                extract('month', Payment.processed_at).label('month'),
                func.sum(Payment.amount).label('revenue'),
                func.count(Payment.id).label('transactions')
            ).filter(
                Payment.status == 'Completed',
                extract('year', Payment.processed_at) == year
            ).group_by(
                extract('month', Payment.processed_at)
            ).order_by('month')
            
            results = query.all()
            
            # Initialize all months with 0 values
            monthly_data = {month: {'revenue': 0, 'transactions': 0} for month in range(1, 13)}
            
            # Fill in actual data
            for month, revenue, transactions in results:
                monthly_data[int(month)] = {
                    'revenue': float(revenue or 0),
                    'transactions': transactions
                }
            
            return monthly_data
            
        except Exception as e:
            logger.error(f"Failed to get monthly revenue: {str(e)}")
            return {month: {'revenue': 0, 'transactions': 0} for month in range(1, 13)}
    
    def get_daily_revenue(self, days=30):
        """Get daily revenue for the last N days"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = db.session.query(
                func.date(Payment.processed_at).label('date'),
                func.sum(Payment.amount).label('revenue'),
                func.count(Payment.id).label('transactions')
            ).filter(
                Payment.status == 'Completed',
                Payment.processed_at >= start_date
            ).group_by(
                func.date(Payment.processed_at)
            ).order_by('date')
            
            results = query.all()
            
            # Convert to dictionary
            daily_data = {}
            for date, revenue, transactions in results:
                daily_data[date.strftime('%Y-%m-%d')] = {
                    'revenue': float(revenue or 0),
                    'transactions': transactions
                }
            
            return daily_data
            
        except Exception as e:
            logger.error(f"Failed to get daily revenue: {str(e)}")
            return {}
    
    def get_top_tutors_by_earnings(self, limit=10, start_date=None, end_date=None):
        """Get top tutors by earnings"""
        try:
            query = db.session.query(
                TutorProfile.id,
                TutorProfile.title,
                User.first_name,
                User.last_name,
                func.sum(Payment.amount).label('total_earnings'),
                func.count(Payment.id).label('total_bookings')
            ).join(Booking).join(User).join(Payment).filter(
                Payment.status == 'Completed'
            )
            
            # Apply date filters
            if start_date:
                query = query.filter(Payment.processed_at >= start_date)
            if end_date:
                query = query.filter(Payment.processed_at <= end_date)
            
            results = query.group_by(
                TutorProfile.id, TutorProfile.title, User.first_name, User.last_name
            ).order_by(func.sum(Payment.amount).desc()).limit(limit).all()
            
            top_tutors = []
            for tutor_id, title, first_name, last_name, earnings, bookings in results:
                top_tutors.append({
                    'tutor_id': tutor_id,
                    'title': title,
                    'name': f"{first_name} {last_name}",
                    'total_earnings': float(earnings or 0),
                    'total_bookings': bookings
                })
            
            return top_tutors
            
        except Exception as e:
            logger.error(f"Failed to get top tutors by earnings: {str(e)}")
            return []
    
    def get_payment_status_distribution(self, start_date=None, end_date=None):
        """Get distribution of payment statuses"""
        try:
            query = db.session.query(
                Payment.status,
                func.count(Payment.id).label('count'),
                func.sum(Payment.amount).label('total_amount')
            )
            
            # Apply date filters
            if start_date:
                query = query.filter(Payment.created_at >= start_date)
            if end_date:
                query = query.filter(Payment.created_at <= end_date)
            
            results = query.group_by(Payment.status).all()
            
            status_distribution = {}
            for status, count, total_amount in results:
                status_distribution[status] = {
                    'count': count,
                    'total_amount': float(total_amount or 0)
                }
            
            return status_distribution
            
        except Exception as e:
            logger.error(f"Failed to get payment status distribution: {str(e)}")
            return {}
    
    def get_payout_analytics(self, start_date=None, end_date=None):
        """Get payout analytics"""
        try:
            query = db.session.query(
                Payout.status,
                func.count(Payout.id).label('count'),
                func.sum(Payout.amount).label('total_amount')
            )
            
            # Apply date filters
            if start_date:
                query = query.filter(Payout.created_at >= start_date)
            if end_date:
                query = query.filter(Payout.created_at <= end_date)
            
            results = query.group_by(Payout.status).all()
            
            payout_analytics = {}
            for status, count, total_amount in results:
                payout_analytics[status] = {
                    'count': count,
                    'total_amount': float(total_amount or 0)
                }
            
            return payout_analytics
            
        except Exception as e:
            logger.error(f"Failed to get payout analytics: {str(e)}")
            return {}
    
    def get_transaction_trends(self, days=30):
        """Get transaction trends over time"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = db.session.query(
                func.date(Payment.created_at).label('date'),
                func.count(Payment.id).label('total_transactions'),
                func.sum(func.case([(Payment.status == 'Completed', Payment.amount)], else_=0)).label('successful_amount'),
                func.sum(func.case([(Payment.status == 'Failed', Payment.amount)], else_=0)).label('failed_amount')
            ).filter(
                Payment.created_at >= start_date
            ).group_by(
                func.date(Payment.created_at)
            ).order_by('date')
            
            results = query.all()
            
            # Convert to dictionary
            trends = {}
            for date, total, successful, failed in results:
                trends[date.strftime('%Y-%m-%d')] = {
                    'total_transactions': total,
                    'successful_amount': float(successful or 0),
                    'failed_amount': float(failed or 0),
                    'success_rate': (successful / (successful + failed) * 100) if (successful + failed) > 0 else 0
                }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get transaction trends: {str(e)}")
            return {}
    
    def get_user_payment_analytics(self, user_id, start_date=None, end_date=None):
        """Get payment analytics for a specific user"""
        try:
            query = db.session.query(
                Payment.status,
                func.count(Payment.id).label('count'),
                func.sum(Payment.amount).label('total_amount')
            ).filter(
                Payment.booking_id.in_(
                    db.session.query(Booking.id).filter(
                        Booking.student_id == user_id
                    )
                )
            )
            
            # Apply date filters
            if start_date:
                query = query.filter(Payment.created_at >= start_date)
            if end_date:
                query = query.filter(Payment.created_at <= end_date)
            
            results = query.group_by(Payment.status).all()
            
            analytics = {}
            for status, count, total_amount in results:
                analytics[status] = {
                    'count': count,
                    'total_amount': float(total_amount or 0)
                }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get user payment analytics: {str(e)}")
            return {}
    
    def get_tutor_earnings_analytics(self, tutor_id, start_date=None, end_date=None):
        """Get earnings analytics for a specific tutor"""
        try:
            query = db.session.query(
                func.sum(Payment.amount).label('total_earnings'),
                func.count(Payment.id).label('total_bookings'),
                func.avg(Payment.amount).label('average_earning_per_booking')
            ).join(Booking).filter(
                Payment.status == 'Completed',
                Booking.tutor_id == tutor_id
            )
            
            # Apply date filters
            if start_date:
                query = query.filter(Payment.processed_at >= start_date)
            if end_date:
                query = query.filter(Payment.processed_at <= end_date)
            
            result = query.first()
            
            return {
                'total_earnings': float(result.total_earnings or 0),
                'total_bookings': result.total_bookings or 0,
                'average_earning_per_booking': float(result.average_earning_per_booking or 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get tutor earnings analytics: {str(e)}")
            return {
                'total_earnings': 0,
                'total_bookings': 0,
                'average_earning_per_booking': 0
            }
    
    def export_payment_data(self, format='csv', start_date=None, end_date=None, status=None):
        """Export payment data in specified format"""
        try:
            query = db.session.query(
                Payment.id,
                Payment.transaction_id,
                Payment.amount,
                Payment.currency,
                Payment.status,
                Payment.payment_gateway,
                Payment.processed_at,
                Payment.created_at,
                Booking.student_id,
                Booking.tutor_id,
                User.email.label('student_email')
            ).join(Booking).join(User, Booking.student_id == User.id)
            
            # Apply filters
            if start_date:
                query = query.filter(Payment.created_at >= start_date)
            if end_date:
                query = query.filter(Payment.created_at <= end_date)
            if status:
                query = query.filter(Payment.status == status)
            
            payments = query.all()
            
            if format.lower() == 'csv':
                return self._export_to_csv(payments)
            elif format.lower() == 'json':
                return self._export_to_json(payments)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export payment data: {str(e)}")
            return None
    
    def _export_to_csv(self, payments):
        """Export payment data to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Transaction ID', 'Amount', 'Currency', 'Status',
            'Payment Gateway', 'Processed At', 'Created At',
            'Student ID', 'Tutor ID', 'Student Email'
        ])
        
        # Write data rows
        for payment in payments:
            writer.writerow([
                payment.id, payment.transaction_id, payment.amount, payment.currency,
                payment.status, payment.payment_gateway, payment.processed_at,
                payment.created_at, payment.student_id, payment.tutor_id, payment.student_email
            ])
        
        return output.getvalue()
    
    def _export_to_json(self, payments):
        """Export payment data to JSON format"""
        import json
        
        data = []
        for payment in payments:
            data.append({
                'id': payment.id,
                'transaction_id': payment.transaction_id,
                'amount': float(payment.amount),
                'currency': payment.currency,
                'status': payment.status,
                'payment_gateway': payment.payment_gateway,
                'processed_at': payment.processed_at.isoformat() if payment.processed_at else None,
                'created_at': payment.created_at.isoformat(),
                'student_id': payment.student_id,
                'tutor_id': payment.tutor_id,
                'student_email': payment.student_email
            })
        
        return json.dumps(data, indent=2)