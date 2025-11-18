from datetime import datetime, timedelta
from decimal import Decimal
from flask import current_app, url_for
from app import db
from app.models.payment import Payout, PaymentMethod
from app.models.tutor import TutorProfile
from app.models.user import User
from app.payment.paypal import PayPalService
from app.payment.upi import UPIService
import logging

logger = logging.getLogger(__name__)

class PayoutService:
    """Service for handling tutor payouts"""
    
    def __init__(self):
        self.paypal_service = PayPalService()
        self.upi_service = UPIService()
    
    def create_payout_request(self, tutor_id, amount, payout_method, payout_details, notes=None):
        """Create a new payout request"""
        try:
            # Validate tutor exists
            tutor = TutorProfile.query.get(tutor_id)
            if not tutor:
                raise Exception("Tutor profile not found")
            
            # Validate minimum payout amount
            min_amount = current_app.config.get('MIN_PAYOUT_AMOUNT', 10.00)
            if amount < min_amount:
                raise Exception(f"Minimum payout amount is ${min_amount}")
            
            # Check if tutor has sufficient earnings
            # This would typically involve calculating available earnings
            # For now, we'll assume they have sufficient funds
            
            # Create payout record
            payout = Payout(
                tutor_id=tutor_id,
                amount=amount,
                currency='USD',  # Default currency, can be made configurable
                payout_method=payout_method,
                payout_details=payout_details,
                status='Pending'
            )
            
            db.session.add(payout)
            db.session.commit()
            
            logger.info(f"Created payout request: {payout.id} for tutor: {tutor_id}")
            return payout
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create payout request: {str(e)}")
            raise Exception(f"Failed to create payout request: {str(e)}")
    
    def process_payout(self, payout_id):
        """Process a pending payout"""
        try:
            payout = Payout.query.get(payout_id)
            if not payout:
                raise Exception("Payout not found")
            
            if payout.status != 'Pending':
                raise Exception("Payout is not in pending status")
            
            # Update status to processing
            payout.status = 'Processing'
            db.session.commit()
            
            # Process payout based on method
            if payout.payout_method == 'PayPal':
                result = self._process_paypal_payout(payout)
            elif payout.payout_method == 'UPI':
                result = self._process_upi_payout(payout)
            elif payout.payout_method == 'Bank Transfer':
                result = self._process_bank_transfer_payout(payout)
            else:
                raise Exception(f"Unsupported payout method: {payout.payout_method}")
            
            if result['status'] == 'success':
                payout.status = 'Completed'
                payout.reference_id = result.get('reference_id')
                payout.processed_at = datetime.utcnow()
            else:
                payout.status = 'Failed'
                payout.failure_reason = result.get('error', 'Unknown error')
            
            db.session.commit()
            logger.info(f"Processed payout: {payout_id} with status: {payout.status}")
            return payout
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to process payout: {str(e)}")
            
            # Mark payout as failed
            if 'payout' in locals():
                payout.status = 'Failed'
                payout.failure_reason = str(e)
                db.session.commit()
            
            raise Exception(f"Failed to process payout: {str(e)}")
    
    def _process_paypal_payout(self, payout):
        """Process PayPal payout"""
        try:
            # This would typically use PayPal's Payouts API
            # For now, we'll simulate the process
            
            # Extract PayPal email from payout details
            paypal_email = payout.payout_details
            
            # Validate PayPal email format
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, paypal_email):
                raise Exception("Invalid PayPal email address")
            
            # Simulate PayPal payout processing
            # In a real implementation, you would use PayPal's Payouts SDK
            reference_id = f"PP_PAYOUT_{payout.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            logger.info(f"Processed PayPal payout: {reference_id}")
            return {
                'status': 'success',
                'reference_id': reference_id
            }
            
        except Exception as e:
            logger.error(f"Failed to process PayPal payout: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _process_upi_payout(self, payout):
        """Process UPI payout"""
        try:
            # Extract UPI ID from payout details
            upi_id = payout.payout_details
            
            # Validate UPI ID
            if not self.upi_service.validate_upi_id(upi_id):
                raise Exception("Invalid UPI ID format")
            
            # Simulate UPI payout processing
            # In a real implementation, you would use Razorpay's Payouts API
            reference_id = f"UPI_PAYOUT_{payout.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            logger.info(f"Processed UPI payout: {reference_id}")
            return {
                'status': 'success',
                'reference_id': reference_id
            }
            
        except Exception as e:
            logger.error(f"Failed to process UPI payout: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _process_bank_transfer_payout(self, payout):
        """Process bank transfer payout"""
        try:
            # Parse bank details from payout_details
            # This would typically contain bank account number, IFSC code, etc.
            bank_details = payout.payout_details
            
            # Validate bank details format
            if not bank_details or len(bank_details) < 10:
                raise Exception("Invalid bank details")
            
            # Simulate bank transfer processing
            # In a real implementation, you would integrate with a banking API
            reference_id = f"BANK_PAYOUT_{payout.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            logger.info(f"Processed bank transfer payout: {reference_id}")
            return {
                'status': 'success',
                'reference_id': reference_id
            }
            
        except Exception as e:
            logger.error(f"Failed to process bank transfer payout: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def get_tutor_payouts(self, tutor_id, status=None, limit=50, offset=0):
        """Get payouts for a specific tutor"""
        query = Payout.query.filter_by(tutor_id=tutor_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Payout.created_at.desc()).limit(limit).offset(offset).all()
    
    def get_all_payouts(self, status=None, limit=50, offset=0):
        """Get all payouts (for admin)"""
        query = Payout.query
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Payout.created_at.desc()).limit(limit).offset(offset).all()
    
    def calculate_tutor_earnings(self, tutor_id, start_date=None, end_date=None):
        """Calculate tutor earnings for a given period"""
        try:
            from app.models.payment import Payment
            from sqlalchemy import func
            
            # Base query for completed payments
            query = db.session.query(
                func.sum(Payment.amount).label('total_earnings'),
                func.count(Payment.id).label('total_bookings')
            ).join(Booking).filter(
                Payment.status == 'Completed',
                Booking.tutor_id == tutor_id
            )
            
            # Apply date filters if provided
            if start_date:
                query = query.filter(Payment.processed_at >= start_date)
            if end_date:
                query = query.filter(Payment.processed_at <= end_date)
            
            result = query.first()
            
            return {
                'total_earnings': float(result.total_earnings or 0),
                'total_bookings': result.total_bookings or 0
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate tutor earnings: {str(e)}")
            return {
                'total_earnings': 0,
                'total_bookings': 0
            }
    
    def get_payout_statistics(self, tutor_id=None):
        """Get payout statistics"""
        try:
            query = db.session.query(
                Payout.status,
                func.count(Payout.id).label('count'),
                func.sum(Payout.amount).label('total_amount')
            )
            
            if tutor_id:
                query = query.filter_by(tutor_id=tutor_id)
            
            results = query.group_by(Payout.status).all()
            
            statistics = {}
            for status, count, total_amount in results:
                statistics[status] = {
                    'count': count,
                    'total_amount': float(total_amount or 0)
                }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to get payout statistics: {str(e)}")
            return {}
    
    def schedule_payout_processing(self):
        """Schedule automatic processing of pending payouts"""
        try:
            # Get pending payouts that are ready for processing
            processing_delay = current_app.config.get('PAYOUT_PROCESSING_DELAY_HOURS', 24)
            cutoff_time = datetime.utcnow() - timedelta(hours=processing_delay)
            
            pending_payouts = Payout.query.filter(
                Payout.status == 'Pending',
                Payout.created_at <= cutoff_time
            ).all()
            
            processed_count = 0
            for payout in pending_payouts:
                try:
                    self.process_payout(payout.id)
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to process scheduled payout {payout.id}: {str(e)}")
            
            logger.info(f"Scheduled processing completed. Processed {processed_count} payouts.")
            return processed_count
            
        except Exception as e:
            logger.error(f"Failed to schedule payout processing: {str(e)}")
            return 0

def create_payout_method(tutor_id, method_type, account_holder_name, account_details, bank_name=None, ifsc_code=None):
    """Create a new payout method for a tutor"""
    try:
        # Validate tutor exists
        tutor = TutorProfile.query.get(tutor_id)
        if not tutor:
            raise Exception("Tutor profile not found")
        
        # Create payout method details string
        if method_type == 'Bank Transfer':
            payout_details = f"{account_holder_name}|{account_details}|{bank_name or ''}|{ifsc_code or ''}"
        elif method_type == 'UPI':
            payout_details = f"{account_holder_name}|{account_details}"
        elif method_type == 'PayPal':
            payout_details = f"{account_holder_name}|{account_details}"
        else:
            raise Exception(f"Unsupported payout method type: {method_type}")
        
        # Create payment method record
        payment_method = PaymentMethod(
            user_id=tutor.user_id,
            payment_type=method_type,
            method_details=payout_details,
            is_default=False
        )
        
        db.session.add(payment_method)
        db.session.commit()
        
        logger.info(f"Created payout method: {payment_method.id} for tutor: {tutor_id}")
        return payment_method
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create payout method: {str(e)}")
        raise Exception(f"Failed to create payout method: {str(e)}")

def get_tutor_payout_methods(tutor_id):
    """Get all payout methods for a tutor"""
    try:
        tutor = TutorProfile.query.get(tutor_id)
        if not tutor:
            raise Exception("Tutor profile not found")
        
        return PaymentMethod.query.filter_by(
            user_id=tutor.user_id
        ).filter(
            PaymentMethod.payment_type.in_(['Bank Transfer', 'UPI', 'PayPal'])
        ).all()
        
    except Exception as e:
        logger.error(f"Failed to get tutor payout methods: {str(e)}")
        return []