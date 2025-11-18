from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

from app.payment.upi import UPIService, create_upi_payment, process_upi_payment_success, process_upi_payment_failure
from app.payment.paypal import PayPalService, create_paypal_payment, process_paypal_payment_success, process_paypal_payment_failure
from app.payment.payouts import PayoutService
from app.payment.analytics import PaymentAnalytics
from app.payment.security import PaymentSecurity
from app.models.payment import Payment, PaymentMethod, Transaction, Payout
from app.models.booking import Booking
from app.models.tutor import TutorProfile
from app.models.user import User
from app.utils.decorators import role_required, api_key_required
from app import db
from app import limiter

# Create blueprint
payment_api = Blueprint('payment_api', __name__, url_prefix='/api/payment')

# Initialize services
upi_service = UPIService()
paypal_service = PayPalService()
payout_service = PayoutService()
payment_analytics = PaymentAnalytics()

# Rate limiting
@payment_api.before_request
@limiter.limit("100 per hour")
def before_request():
    """Apply rate limiting to all payment API endpoints"""
    pass

@payment_api.route('/methods', methods=['GET'])
@login_required
def get_payment_methods():
    """Get user's payment methods"""
    try:
        payment_methods = PaymentMethod.query.filter_by(user_id=current_user.id).all()
        
        methods_data = []
        for method in payment_methods:
            methods_data.append({
                'id': method.id,
                'payment_type': method.payment_type,
                'method_details': method.method_details,
                'is_default': method.is_default,
                'is_active': method.is_active,
                'created_at': method.created_at.isoformat()
            })
        
        return jsonify({
            'status': 'success',
            'payment_methods': methods_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/methods', methods=['POST'])
@login_required
def add_payment_method():
    """Add a new payment method"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('payment_type') or not data.get('method_details'):
            return jsonify({
                'status': 'error',
                'message': 'Payment type and method details are required'
            }), 400
        
        # Create payment method
        payment_method = PaymentMethod(
            user_id=current_user.id,
            payment_type=data['payment_type'],
            method_details=data['method_details'],
            is_default=data.get('is_default', False)
        )
        
        # If set as default, unset other defaults
        if payment_method.is_default:
            PaymentMethod.query.filter_by(user_id=current_user.id).update({'is_default': False})
        
        db.session.add(payment_method)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Payment method added successfully',
            'payment_method': {
                'id': payment_method.id,
                'payment_type': payment_method.payment_type,
                'method_details': payment_method.method_details,
                'is_default': payment_method.is_default,
                'is_active': payment_method.is_active,
                'created_at': payment_method.created_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/upi/order', methods=['POST'])
@login_required
def create_upi_order():
    """Create UPI payment order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['booking_id', 'upi_id', 'amount']):
            return jsonify({
                'status': 'error',
                'message': 'Booking ID, UPI ID, and amount are required'
            }), 400
        
        # Validate UPI ID
        valid, error = PaymentSecurity.validate_upi_id(data['upi_id'])
        if not valid:
            return jsonify({
                'status': 'error',
                'message': error
            }), 400
        
        # Get booking
        booking = Booking.query.get(data['booking_id'])
        if not booking:
            return jsonify({
                'status': 'error',
                'message': 'Booking not found'
            }), 404
        
        # Check ownership
        if booking.student_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access to booking'
            }), 403
        
        # Create payment record
        payment = create_upi_payment(
            user_id=current_user.id,
            booking_id=data['booking_id'],
            upi_id=data['upi_id'],
            amount=float(data['amount']),
            description=data.get('description')
        )
        
        # Create Razorpay order
        order = upi_service.create_upi_order(
            amount=float(data['amount']),
            currency='INR',
            description=data.get('description'),
            booking_id=data['booking_id'],
            user_id=current_user.id
        )
        
        # Generate QR code
        qr_data = upi_service.generate_upi_qr_code(
            upi_id=data['upi_id'],
            amount=float(data['amount']),
            description=data.get('description'),
            order_id=order['id']
        )
        
        return jsonify({
            'status': 'success',
            'payment': {
                'id': payment.id,
                'transaction_id': payment.transaction_id,
                'amount': float(payment.amount),
                'currency': payment.currency
            },
            'order': order,
            'qr_code': qr_data['qr_code'],
            'upi_url': qr_data['upi_url']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/upi/verify', methods=['POST'])
@login_required
def verify_upi_payment():
    """Verify UPI payment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['payment_id', 'razorpay_payment_id', 'razorpay_order_id']):
            return jsonify({
                'status': 'error',
                'message': 'Payment ID, Razorpay Payment ID, and Order ID are required'
            }), 400
        
        # Verify payment with Razorpay
        verification = upi_service.verify_upi_payment(
            data['razorpay_payment_id'], 
            data['razorpay_order_id']
        )
        
        if verification['status'] == 'success':
            # Process successful payment
            payment = process_upi_payment_success(
                data['payment_id'], 
                data['razorpay_payment_id'], 
                data['razorpay_order_id']
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Payment verified successfully',
                'payment': {
                    'id': payment.id,
                    'status': payment.status,
                    'processed_at': payment.processed_at.isoformat() if payment.processed_at else None
                }
            })
        else:
            # Process failed payment
            process_upi_payment_failure(data['payment_id'], verification['error'])
            
            return jsonify({
                'status': 'failed',
                'message': verification['error']
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/paypal/order', methods=['POST'])
@login_required
def create_paypal_order():
    """Create PayPal payment order"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['booking_id', 'paypal_email', 'amount']):
            return jsonify({
                'status': 'error',
                'message': 'Booking ID, PayPal email, and amount are required'
            }), 400
        
        # Validate PayPal email
        valid, error = PaymentSecurity.validate_paypal_email(data['paypal_email'])
        if not valid:
            return jsonify({
                'status': 'error',
                'message': error
            }), 400
        
        # Get booking
        booking = Booking.query.get(data['booking_id'])
        if not booking:
            return jsonify({
                'status': 'error',
                'message': 'Booking not found'
            }), 404
        
        # Check ownership
        if booking.student_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access to booking'
            }), 403
        
        # Create payment record
        payment = create_paypal_payment(
            user_id=current_user.id,
            booking_id=data['booking_id'],
            paypal_email=data['paypal_email'],
            amount=float(data['amount']),
            description=data.get('description')
        )
        
        # Create PayPal order
        order_data = paypal_service.create_order(
            amount=float(data['amount']),
            currency='USD',
            description=data.get('description'),
            booking_id=data['booking_id'],
            user_id=current_user.id
        )
        
        return jsonify({
            'status': 'success',
            'payment': {
                'id': payment.id,
                'transaction_id': payment.transaction_id,
                'amount': float(payment.amount),
                'currency': payment.currency
            },
            'order': {
                'id': order_data['order_id'],
                'approval_url': order_data['approval_url']
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/paypal/capture/<order_id>', methods=['POST'])
@login_required
def capture_paypal_order(order_id):
    """Capture PayPal payment"""
    try:
        # Capture the payment
        capture_result = paypal_service.capture_order(order_id)
        
        if capture_result['status'] == 'success':
            # Find the corresponding payment record
            # This is a simplified approach - in production, you'd track order ID
            payment = Payment.query.filter_by(
                transaction_id=capture_result['payment_id']
            ).first()
            
            if payment:
                # Process successful payment
                process_paypal_payment_success(
                    payment.transaction_id,
                    order_id,
                    capture_result['payment_id']
                )
                
                return jsonify({
                    'status': 'success',
                    'message': 'Payment captured successfully',
                    'payment': {
                        'id': payment.id,
                        'status': payment.status,
                        'processed_at': payment.processed_at.isoformat() if payment.processed_at else None
                    }
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Payment record not found'
                }), 404
        else:
            return jsonify({
                'status': 'failed',
                'message': capture_result['error']
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/history', methods=['GET'])
@login_required
def get_payment_history():
    """Get payment history"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        payment_method = request.args.get('payment_method')
        
        # Build query
        query = db.session.query(Payment).join(Booking)
        
        # Filter based on user role
        if current_user.role == 'tutor':
            query = query.filter(Booking.tutor_id == current_user.tutor_profile.id)
        else:
            query = query.filter(Booking.student_id == current_user.id)
        
        # Apply filters
        if status:
            query = query.filter(Payment.status == status)
        
        if payment_method:
            query = query.join(PaymentMethod).filter(
                PaymentMethod.payment_type == payment_method
            )
        
        # Paginate
        payments = query.order_by(Payment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        payments_data = []
        for payment in payments.items:
            payments_data.append({
                'id': payment.id,
                'transaction_id': payment.transaction_id,
                'amount': float(payment.amount),
                'currency': payment.currency,
                'status': payment.status,
                'payment_gateway': payment.payment_gateway,
                'payment_method': payment.payment_method.payment_type if payment.payment_method else None,
                'created_at': payment.created_at.isoformat(),
                'processed_at': payment.processed_at.isoformat() if payment.processed_at else None,
                'booking_id': payment.booking_id
            })
        
        return jsonify({
            'status': 'success',
            'payments': payments_data,
            'pagination': {
                'page': payments.page,
                'per_page': payments.per_page,
                'total': payments.total,
                'pages': payments.pages,
                'has_prev': payments.has_prev,
                'has_next': payments.has_next
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/refund', methods=['POST'])
@login_required
def process_refund():
    """Process payment refund"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['payment_id', 'refund_amount', 'refund_reason']):
            return jsonify({
                'status': 'error',
                'message': 'Payment ID, refund amount, and refund reason are required'
            }), 400
        
        # Get payment
        payment = Payment.query.get(data['payment_id'])
        if not payment:
            return jsonify({
                'status': 'error',
                'message': 'Payment not found'
            }), 404
        
        # Check ownership and permissions
        if current_user.role == 'tutor':
            if payment.booking.tutor_id != current_user.tutor_profile.id:
                return jsonify({
                    'status': 'error',
                    'message': 'Unauthorized access'
                }), 403
        elif current_user.role != 'admin':
            if payment.booking.student_id != current_user.id:
                return jsonify({
                    'status': 'error',
                    'message': 'Unauthorized access'
                }), 403
        
        # Check if payment can be refunded
        if payment.status != 'Completed':
            return jsonify({
                'status': 'error',
                'message': 'Only completed payments can be refunded'
            }), 400
        
        # Process refund based on payment gateway
        if payment.payment_gateway == 'PayPal':
            refund_result = paypal_service.process_refund(
                payment.gateway_transaction_id,
                float(data['refund_amount'])
            )
        elif payment.payment_gateway == 'Razorpay':
            refund_result = upi_service.process_upi_refund(
                payment.gateway_transaction_id,
                float(data['refund_amount'])
            )
        else:
            return jsonify({
                'status': 'error',
                'message': 'Refund not supported for this payment method'
            }), 400
        
        if refund_result['status'] == 'success':
            # Update payment status
            payment.status = 'Refunded'
            
            # Create refund transaction
            refund_transaction = Transaction(
                payment_id=payment.id,
                amount=float(data['refund_amount']),
                currency=payment.currency,
                transaction_type='Refund',
                description=data['refund_reason'],
                status='Completed',
                reference_id=refund_result.get('refund_id')
            )
            db.session.add(refund_transaction)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Refund processed successfully',
                'refund': {
                    'id': refund_transaction.id,
                    'amount': float(refund_transaction.amount),
                    'currency': refund_transaction.currency,
                    'reference_id': refund_transaction.reference_id
                }
            })
        else:
            return jsonify({
                'status': 'failed',
                'message': refund_result['error']
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/payouts', methods=['GET'])
@login_required
@role_required('tutor', 'admin')
def get_payouts():
    """Get payouts"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        
        # Build query
        if current_user.role == 'tutor':
            payouts = payout_service.get_tutor_payouts(
                current_user.tutor_profile.id,
                status=status,
                limit=per_page,
                offset=(page - 1) * per_page
            )
        else:
            payouts = payout_service.get_all_payouts(
                status=status,
                limit=per_page,
                offset=(page - 1) * per_page
            )
        
        payouts_data = []
        for payout in payouts:
            payouts_data.append({
                'id': payout.id,
                'amount': float(payout.amount),
                'currency': payout.currency,
                'payout_method': payout.payout_method,
                'status': payout.status,
                'reference_id': payout.reference_id,
                'created_at': payout.created_at.isoformat(),
                'processed_at': payout.processed_at.isoformat() if payout.processed_at else None
            })
        
        return jsonify({
            'status': 'success',
            'payouts': payouts_data
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/payouts', methods=['POST'])
@login_required
@role_required('tutor')
def request_payout():
    """Request a payout"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(k in data for k in ['amount', 'payout_method', 'payout_details']):
            return jsonify({
                'status': 'error',
                'message': 'Amount, payout method, and payout details are required'
            }), 400
        
        # Validate payout amount
        valid, error = PaymentSecurity.validate_amount(data['amount'])
        if not valid:
            return jsonify({
                'status': 'error',
                'message': error
            }), 400
        
        # Create payout request
        payout = payout_service.create_payout_request(
            tutor_id=current_user.tutor_profile.id,
            amount=float(data['amount']),
            payout_method=data['payout_method'],
            payout_details=data['payout_details'],
            notes=data.get('notes')
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Payout request submitted successfully',
            'payout': {
                'id': payout.id,
                'amount': float(payout.amount),
                'currency': payout.currency,
                'payout_method': payout.payout_method,
                'status': payout.status,
                'created_at': payout.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/analytics/revenue', methods=['GET'])
@login_required
@role_required('admin')
def get_revenue_analytics():
    """Get revenue analytics"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        currency = request.args.get('currency')
        
        # Parse dates
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get analytics data
        revenue_summary = payment_analytics.get_revenue_summary(start_date, end_date, currency)
        payment_method_analytics = payment_analytics.get_payment_method_analytics(start_date, end_date)
        
        return jsonify({
            'status': 'success',
            'revenue_summary': revenue_summary,
            'payment_method_analytics': payment_method_analytics
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/webhooks/paypal', methods=['POST'])
@api_key_required
def paypal_webhook():
    """Handle PayPal webhooks"""
    try:
        # Get webhook data
        data = request.get_json()
        
        # Get headers for verification
        headers = request.headers
        
        # Verify webhook signature
        if not paypal_service.verify_webhook(headers, json.dumps(data)):
            return jsonify({'status': 'error', 'message': 'Invalid webhook signature'}), 401
        
        # Process webhook event
        event_type = data.get('event_type')
        resource = data.get('resource', {})
        webhook_event_id = data.get('id')
        
        if paypal_service.handle_paypal_webhook(event_type, resource, webhook_event_id):
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to process webhook'}), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@payment_api.route('/webhooks/razorpay', methods=['POST'])
@api_key_required
def razorpay_webhook():
    """Handle Razorpay webhooks"""
    try:
        # Get webhook data
        data = request.get_json()
        
        # Verify webhook signature
        # This would involve verifying the signature using Razorpay's webhook secret
        
        # Process webhook event
        event_type = data.get('event')
        
        if event_type == 'payment.captured':
            # Payment captured successfully
            payment_data = data.get('payload', {}).get('payment', {})
            razorpay_payment_id = payment_data.get('id')
            razorpay_order_id = payment_data.get('order_id')
            
            # Find the corresponding payment record
            payment = Payment.query.filter_by(
                gateway_transaction_id=razorpay_payment_id
            ).first()
            
            if payment:
                process_upi_payment_success(
                    payment.transaction_id,
                    razorpay_payment_id,
                    razorpay_order_id
                )
                
        elif event_type == 'payment.failed':
            # Payment failed
            payment_data = data.get('payload', {}).get('payment', {})
            razorpay_payment_id = payment_data.get('id')
            
            # Find the corresponding payment record
            payment = Payment.query.filter_by(
                gateway_transaction_id=razorpay_payment_id
            ).first()
            
            if payment:
                failure_reason = payment_data.get('error', {}).get('description', 'Payment failed')
                process_upi_payment_failure(payment.transaction_id, failure_reason)
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500