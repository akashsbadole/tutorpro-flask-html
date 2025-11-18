import qrcode
import io
import base64
import razorpay
import requests
from datetime import datetime, timedelta
from flask import current_app, url_for
from app import db
from app.models.payment import Payment, PaymentMethod, Transaction
from app.models.booking import Booking
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

class UPIService:
    """Service for handling UPI payments through Razorpay"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Razorpay client"""
        try:
            key_id = current_app.config.get('RAZORPAY_KEY_ID')
            key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')
            
            if key_id and key_secret:
                self.client = razorpay.Client(auth=(key_id, key_secret))
                logger.info("Razorpay client initialized successfully")
            else:
                logger.warning("Razorpay credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {str(e)}")
    
    def create_upi_order(self, amount, currency='INR', description=None, booking_id=None, user_id=None):
        """Create a UPI payment order using Razorpay"""
        if not self.client:
            raise Exception("Razorpay client not initialized")
        
        try:
            # Convert amount to paise (Razorpay uses smallest currency unit)
            amount_paise = int(amount * 100)
            
            # Create order data
            order_data = {
                'amount': amount_paise,
                'currency': currency,
                'payment_capture': 1,
                'notes': {
                    'description': description or 'UPI Payment',
                    'booking_id': booking_id,
                    'user_id': user_id
                }
            }
            
            # Create order
            order = self.client.order.create(data=order_data)
            logger.info(f"Created UPI order: {order['id']}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create UPI order: {str(e)}")
            raise Exception(f"Failed to create payment order: {str(e)}")
    
    def generate_upi_qr_code(self, upi_id, amount, currency='INR', description=None, order_id=None):
        """Generate UPI QR code for payment"""
        try:
            # Construct UPI payment URL
            upi_url = f"upi://pay?pa={upi_id}&pn=TutorPro&am={amount}&cu={currency}"
            
            if description:
                upi_url += f"&tn={description}"
            
            if order_id:
                upi_url += f"&tr={order_id}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(upi_url)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for display in HTML
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
            
            return {
                'qr_code': f"data:image/png;base64,{img_base64}",
                'upi_url': upi_url,
                'order_id': order_id
            }
            
        except Exception as e:
            logger.error(f"Failed to generate UPI QR code: {str(e)}")
            raise Exception(f"Failed to generate QR code: {str(e)}")
    
    def validate_upi_id(self, upi_id):
        """Validate UPI ID format"""
        import re
        pattern = r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$'
        return bool(re.match(pattern, upi_id))
    
    def verify_upi_payment(self, payment_id, order_id):
        """Verify UPI payment status"""
        if not self.client:
            raise Exception("Razorpay client not initialized")
        
        try:
            # Fetch payment details
            payment = self.client.payment.fetch(payment_id)
            
            # Check if payment is successful
            if payment.get('status') == 'captured':
                # Verify order matches
                if payment.get('order_id') == order_id:
                    return {
                        'status': 'success',
                        'payment_id': payment_id,
                        'order_id': order_id,
                        'amount': payment.get('amount', 0) / 100,  # Convert back from paise
                        'currency': payment.get('currency', 'INR'),
                        'method': payment.get('method', 'upi'),
                        'email': payment.get('email'),
                        'contact': payment.get('contact')
                    }
            
            return {
                'status': 'failed',
                'error': payment.get('error_description', 'Payment verification failed')
            }
            
        except Exception as e:
            logger.error(f"Failed to verify UPI payment: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def process_upi_refund(self, payment_id, amount=None):
        """Process refund for UPI payment"""
        if not self.client:
            raise Exception("Razorpay client not initialized")
        
        try:
            # Prepare refund data
            refund_data = {'payment_id': payment_id}
            
            if amount:
                # Convert amount to paise
                refund_data['amount'] = int(amount * 100)
            
            # Process refund
            refund = self.client.refund.create(refund_data)
            logger.info(f"Processed UPI refund: {refund['id']}")
            
            return {
                'status': 'success',
                'refund_id': refund['id'],
                'amount': refund.get('amount', 0) / 100,  # Convert back from paise
                'status': refund.get('status', 'processed')
            }
            
        except Exception as e:
            logger.error(f"Failed to process UPI refund: {str(e)}")
            raise Exception(f"Refund processing failed: {str(e)}")
    
    def get_upi_payment_status(self, payment_id):
        """Get status of UPI payment"""
        if not self.client:
            raise Exception("Razorpay client not initialized")
        
        try:
            payment = self.client.payment.fetch(payment_id)
            return {
                'status': payment.get('status'),
                'amount': payment.get('amount', 0) / 100,
                'currency': payment.get('currency', 'INR'),
                'method': payment.get('method', 'upi'),
                'created_at': payment.get('created_at'),
                'captured_at': payment.get('captured_at')
            }
        except Exception as e:
            logger.error(f"Failed to get UPI payment status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

def create_upi_payment(user_id, booking_id, upi_id, amount, description=None):
    """Create a new UPI payment"""
    try:
        # Get or create UPI payment method
        payment_method = PaymentMethod.query.filter_by(
            user_id=user_id, 
            payment_type='UPI', 
            method_details=upi_id
        ).first()
        
        if not payment_method:
            payment_method = PaymentMethod(
                user_id=user_id,
                payment_type='UPI',
                method_details=upi_id,
                is_default=False
            )
            db.session.add(payment_method)
            db.session.flush()
        
        # Create payment record
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            currency='INR',
            payment_method_id=payment_method.id,
            transaction_id=f"UPI_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status='Pending',
            payment_gateway='Razorpay'
        )
        db.session.add(payment)
        db.session.flush()
        
        # Create transaction record
        transaction = Transaction(
            payment_id=payment.id,
            amount=amount,
            currency='INR',
            transaction_type='Payment',
            description=description or f'UPI payment for booking {booking_id}',
            status='Pending'
        )
        db.session.add(transaction)
        db.session.commit()
        
        return payment
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create UPI payment: {str(e)}")
        raise Exception(f"Failed to create payment: {str(e)}")

def process_upi_payment_success(payment_id, razorpay_payment_id, razorpay_order_id):
    """Process successful UPI payment"""
    try:
        # Get payment record
        payment = Payment.query.filter_by(transaction_id=payment_id).first()
        if not payment:
            raise Exception("Payment record not found")
        
        # Update payment status
        payment.status = 'Completed'
        payment.gateway_transaction_id = razorpay_payment_id
        payment.processed_at = datetime.utcnow()
        
        # Update transaction status
        for transaction in payment.transactions:
            transaction.status = 'Completed'
            transaction.completed_at = datetime.utcnow()
            transaction.reference_id = razorpay_order_id
        
        # Update booking status
        booking = Booking.query.get(payment.booking_id)
        if booking:
            booking.status = 'Confirmed'
        
        db.session.commit()
        logger.info(f"Processed successful UPI payment: {payment_id}")
        return payment
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to process UPI payment success: {str(e)}")
        raise Exception(f"Failed to process payment: {str(e)}")

def process_upi_payment_failure(payment_id, failure_reason):
    """Process failed UPI payment"""
    try:
        # Get payment record
        payment = Payment.query.filter_by(transaction_id=payment_id).first()
        if not payment:
            raise Exception("Payment record not found")
        
        # Update payment status
        payment.status = 'Failed'
        payment.failure_reason = failure_reason
        
        # Update transaction status
        for transaction in payment.transactions:
            transaction.status = 'Failed'
        
        db.session.commit()
        logger.info(f"Processed failed UPI payment: {payment_id}")
        return payment
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to process UPI payment failure: {str(e)}")
        raise Exception(f"Failed to process payment failure: {str(e)}")