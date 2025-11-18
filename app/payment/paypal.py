from datetime import datetime, timedelta
from flask import current_app, url_for
from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment, LiveEnvironment
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest
from paypalcheckoutsdk.payments import CapturesRefundRequest
from app import db
from app.models.payment import Payment, PaymentMethod, Transaction
from app.models.booking import Booking
import logging
import json

logger = logging.getLogger(__name__)

class PayPalService:
    """Service for handling PayPal payments"""
    
    def __init__(self):
        self.client = None
        self.environment = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize PayPal client"""
        try:
            client_id = current_app.config.get('PAYPAL_CLIENT_ID')
            client_secret = current_app.config.get('PAYPAL_CLIENT_SECRET')
            environment_type = current_app.config.get('PAYPAL_ENVIRONMENT', 'sandbox')
            
            if client_id and client_secret:
                # Set up environment
                if environment_type == 'sandbox':
                    self.environment = SandboxEnvironment(client_id=client_id, client_secret=client_secret)
                else:
                    self.environment = LiveEnvironment(client_id=client_id, client_secret=client_secret)
                
                self.client = PayPalHttpClient(self.environment)
                logger.info(f"PayPal client initialized for {environment_type} environment")
            else:
                logger.warning("PayPal credentials not configured")
                
        except Exception as e:
            logger.error(f"Failed to initialize PayPal client: {str(e)}")
    
    def create_order(self, amount, currency='USD', description=None, return_url=None, cancel_url=None, booking_id=None, user_id=None):
        """Create a PayPal payment order"""
        if not self.client:
            raise Exception("PayPal client not initialized")
        
        try:
            # Set default return and cancel URLs if not provided
            if not return_url:
                return_url = url_for('payment.paypal_success', _external=True)
            if not cancel_url:
                cancel_url = url_for('payment.paypal_cancel', _external=True)
            
            # Create order request
            request = OrdersCreateRequest()
            request.prefer("return=representation")
            
            # Build order body
            order_body = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": f"booking_{booking_id}" if booking_id else "payment",
                    "description": description or "TutorPro Payment",
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}"
                    },
                    "custom_id": str(user_id) if user_id else None
                }],
                "application_context": {
                    "cancel_url": cancel_url,
                    "return_url": return_url,
                    "brand_name": "TutorPro",
                    "locale": "en-US",
                    "landing_page": "BILLING",
                    "shipping_preference": "NO_SHIPPING",
                    "user_action": "PAY_NOW"
                }
            }
            
            request.request_body(order_body)
            
            # Execute request
            response = self.client.execute(request)
            order = response.result
            
            logger.info(f"Created PayPal order: {order.id}")
            return {
                'order_id': order.id,
                'status': order.status,
                'approval_url': self._get_approval_url(order),
                'order_data': order
            }
            
        except Exception as e:
            logger.error(f"Failed to create PayPal order: {str(e)}")
            raise Exception(f"Failed to create payment order: {str(e)}")
    
    def _get_approval_url(self, order):
        """Extract approval URL from PayPal order response"""
        for link in order.links:
            if link.rel == "approve":
                return link.href
        return None
    
    def capture_order(self, order_id):
        """Capture payment for approved PayPal order"""
        if not self.client:
            raise Exception("PayPal client not initialized")
        
        try:
            request = OrdersCaptureRequest(order_id)
            response = self.client.execute(request)
            order = response.result
            
            if order.status == "COMPLETED":
                purchase_unit = order.purchase_units[0]
                payment = purchase_unit.payments.captures[0]
                
                return {
                    'status': 'success',
                    'order_id': order_id,
                    'payment_id': payment.id,
                    'amount': float(payment.amount.value),
                    'currency': payment.amount.currency_code,
                    'status': payment.status,
                    'transaction_id': payment.id,
                    'create_time': payment.create_time,
                    'update_time': payment.update_time
                }
            else:
                return {
                    'status': 'failed',
                    'error': f"Order not completed. Status: {order.status}"
                }
                
        except Exception as e:
            logger.error(f"Failed to capture PayPal order: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_order_details(self, order_id):
        """Get details of a PayPal order"""
        if not self.client:
            raise Exception("PayPal client not initialized")
        
        try:
            from paypalcheckoutsdk.orders import OrdersGetRequest
            request = OrdersGetRequest(order_id)
            response = self.client.execute(request)
            return response.result
            
        except Exception as e:
            logger.error(f"Failed to get PayPal order details: {str(e)}")
            return None
    
    def process_refund(self, capture_id, amount=None, currency='USD'):
        """Process refund for PayPal payment"""
        if not self.client:
            raise Exception("PayPal client not initialized")
        
        try:
            request = CapturesRefundRequest(capture_id)
            
            if amount:
                # Partial refund
                request.request_body({
                    "amount": {
                        "value": f"{amount:.2f}",
                        "currency_code": currency
                    }
                })
            
            response = self.client.execute(request)
            refund = response.result
            
            logger.info(f"Processed PayPal refund: {refund.id}")
            return {
                'status': 'success',
                'refund_id': refund.id,
                'amount': float(refund.amount.value),
                'currency': refund.amount.currency_code,
                'status': refund.status,
                'create_time': refund.create_time
            }
            
        except Exception as e:
            logger.error(f"Failed to process PayPal refund: {str(e)}")
            raise Exception(f"Refund processing failed: {str(e)}")
    
    def create_subscription(self, plan_id, return_url=None, cancel_url=None):
        """Create a PayPal subscription (for recurring payments)"""
        if not self.client:
            raise Exception("PayPal client not initialized")
        
        try:
            # This would require additional PayPal subscription setup
            # Implementation would depend on subscription plan configuration
            logger.info("PayPal subscription creation not fully implemented")
            return None
            
        except Exception as e:
            logger.error(f"Failed to create PayPal subscription: {str(e)}")
            raise Exception(f"Subscription creation failed: {str(e)}")
    
    def verify_webhook(self, headers, body):
        """Verify PayPal webhook signature"""
        # Implementation for webhook verification
        # This would require webhook ID and signature verification
        return True  # Simplified for now

def create_paypal_payment(user_id, booking_id, paypal_email, amount, description=None):
    """Create a new PayPal payment"""
    try:
        # Get or create PayPal payment method
        payment_method = PaymentMethod.query.filter_by(
            user_id=user_id, 
            payment_type='PayPal', 
            method_details=paypal_email
        ).first()
        
        if not payment_method:
            payment_method = PaymentMethod(
                user_id=user_id,
                payment_type='PayPal',
                method_details=paypal_email,
                is_default=False
            )
            db.session.add(payment_method)
            db.session.flush()
        
        # Create payment record
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            currency='USD',
            payment_method_id=payment_method.id,
            transaction_id=f"PP_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status='Pending',
            payment_gateway='PayPal'
        )
        db.session.add(payment)
        db.session.flush()
        
        # Create transaction record
        transaction = Transaction(
            payment_id=payment.id,
            amount=amount,
            currency='USD',
            transaction_type='Payment',
            description=description or f'PayPal payment for booking {booking_id}',
            status='Pending'
        )
        db.session.add(transaction)
        db.session.commit()
        
        return payment
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create PayPal payment: {str(e)}")
        raise Exception(f"Failed to create payment: {str(e)}")

def process_paypal_payment_success(payment_id, paypal_order_id, paypal_payment_id):
    """Process successful PayPal payment"""
    try:
        # Get payment record
        payment = Payment.query.filter_by(transaction_id=payment_id).first()
        if not payment:
            raise Exception("Payment record not found")
        
        # Update payment status
        payment.status = 'Completed'
        payment.gateway_transaction_id = paypal_payment_id
        payment.processed_at = datetime.utcnow()
        
        # Update transaction status
        for transaction in payment.transactions:
            transaction.status = 'Completed'
            transaction.completed_at = datetime.utcnow()
            transaction.reference_id = paypal_order_id
            transaction.gateway_response = json.dumps({
                'paypal_order_id': paypal_order_id,
                'paypal_payment_id': paypal_payment_id
            })
        
        # Update booking status
        booking = Booking.query.get(payment.booking_id)
        if booking:
            booking.status = 'Confirmed'
        
        db.session.commit()
        logger.info(f"Processed successful PayPal payment: {payment_id}")
        return payment
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to process PayPal payment success: {str(e)}")
        raise Exception(f"Failed to process payment: {str(e)}")

def process_paypal_payment_failure(payment_id, failure_reason):
    """Process failed PayPal payment"""
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
        logger.info(f"Processed failed PayPal payment: {payment_id}")
        return payment
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to process PayPal payment failure: {str(e)}")
        raise Exception(f"Failed to process payment failure: {str(e)}")

def handle_paypal_webhook(event_type, resource, webhook_event_id):
    """Handle PayPal webhook events"""
    try:
        logger.info(f"Processing PayPal webhook: {event_type}")
        
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            # Payment completed successfully
            capture_id = resource.get('id')
            # Process payment completion logic here
            
        elif event_type == "PAYMENT.CAPTURE.DENIED":
            # Payment was denied
            # Process payment failure logic here
            
        elif event_type == "CHECKOUT.ORDER.APPROVED":
            # Order approved but not yet captured
            # Process order approval logic here
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to handle PayPal webhook: {str(e)}")
        return False