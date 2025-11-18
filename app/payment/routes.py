from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import io
import csv
import json

from app.payment import bp
from app.payment.forms import (
    PaymentMethodForm, UPIPaymentForm, PayPalPaymentForm, PaymentForm,
    RefundForm, PayoutRequestForm, PayoutMethodForm, PaymentSearchForm, AnalyticsFilterForm
)
from app.payment.upi import UPIService, create_upi_payment, process_upi_payment_success, process_upi_payment_failure
from app.payment.paypal import PayPalService, create_paypal_payment, process_paypal_payment_success, process_paypal_payment_failure
from app.payment.payouts import PayoutService, create_payout_method, get_tutor_payout_methods
from app.payment.analytics import PaymentAnalytics
from app.payment.security import PaymentSecurity, require_payment_security
from app.models.payment import Payment, PaymentMethod, Transaction, Payout
from app.models.booking import Booking
from app.models.tutor import TutorProfile
from app.models.user import User
from app.utils.decorators import role_required
from app import db

# Initialize services
upi_service = UPIService()
paypal_service = PayPalService()
payout_service = PayoutService()
payment_analytics = PaymentAnalytics()

@bp.route('/')
@login_required
def index():
    """Payment dashboard"""
    # Get user's payment methods
    payment_methods = PaymentMethod.query.filter_by(user_id=current_user.id).all()
    
    # Get recent payments
    if current_user.role == 'tutor':
        # For tutors, get payments for their bookings
        recent_payments = db.session.query(Payment).join(Booking).filter(
            Booking.tutor_id == current_user.tutor_profile.id
        ).order_by(Payment.created_at.desc()).limit(10).all()
    else:
        # For students, get their payments
        recent_payments = db.session.query(Payment).join(Booking).filter(
            Booking.student_id == current_user.id
        ).order_by(Payment.created_at.desc()).limit(10).all()
    
    return render_template('payment/index.html', 
                          payment_methods=payment_methods,
                          recent_payments=recent_payments)

@bp.route('/methods', methods=['GET', 'POST'])
@login_required
def payment_methods():
    """Manage payment methods"""
    form = PaymentMethodForm()
    
    if form.validate_on_submit():
        try:
            # Create new payment method
            payment_method = PaymentMethod(
                user_id=current_user.id,
                payment_type=form.payment_type.data,
                method_details=form.method_details.data,
                is_default=form.is_default.data
            )
            
            # If set as default, unset other defaults
            if form.is_default.data:
                PaymentMethod.query.filter_by(user_id=current_user.id).update({'is_default': False})
            
            db.session.add(payment_method)
            db.session.commit()
            
            flash('Payment method added successfully!', 'success')
            return redirect(url_for('payment.payment_methods'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding payment method: {str(e)}', 'danger')
    
    # Get existing payment methods
    payment_methods = PaymentMethod.query.filter_by(user_id=current_user.id).all()
    
    return render_template('payment/methods.html', form=form, payment_methods=payment_methods)

@bp.route('/methods/<int:method_id>/delete', methods=['POST'])
@login_required
def delete_payment_method(method_id):
    """Delete a payment method"""
    try:
        payment_method = PaymentMethod.query.get_or_404(method_id)
        
        # Check ownership
        if payment_method.user_id != current_user.id:
            flash('You can only delete your own payment methods', 'danger')
            return redirect(url_for('payment.payment_methods'))
        
        # Check if payment method is used in any payments
        if Payment.query.filter_by(payment_method_id=method_id).first():
            flash('Cannot delete payment method that is used in transactions', 'danger')
            return redirect(url_for('payment.payment_methods'))
        
        db.session.delete(payment_method)
        db.session.commit()
        
        flash('Payment method deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting payment method: {str(e)}', 'danger')
    
    return redirect(url_for('payment.payment_methods'))

@bp.route('/process/<int:booking_id>', methods=['GET', 'POST'])
@login_required
@require_payment_security
def process_payment(booking_id):
    """Process payment for a booking"""
    # Get booking
    booking = Booking.query.get_or_404(booking_id)
    
    # Check ownership
    if booking.student_id != current_user.id:
        flash('You can only pay for your own bookings', 'danger')
        return redirect(url_for('student.dashboard'))
    
    # Check if payment already exists
    existing_payment = Payment.query.filter_by(booking_id=booking_id).first()
    if existing_payment and existing_payment.status == 'Completed':
        flash('Payment already completed for this booking', 'info')
        return redirect(url_for('student.dashboard'))
    
    # Get user's payment methods
    payment_methods = PaymentMethod.query.filter_by(user_id=current_user.id).all()
    
    if not payment_methods:
        flash('Please add a payment method first', 'warning')
        return redirect(url_for('payment.payment_methods'))
    
    form = PaymentForm()
    form.booking_id.data = booking_id
    form.payment_method_id.choices = [(pm.id, f"{pm.payment_type} - {pm.method_details}") for pm in payment_methods]
    
    if form.validate_on_submit():
        try:
            payment_method = PaymentMethod.query.get(form.payment_method_id.data)
            
            # Create payment based on payment type
            if payment_method.payment_type == 'UPI':
                # Redirect to UPI payment page
                return redirect(url_for('payment.upi_payment', booking_id=booking_id, 
                                      payment_method_id=payment_method.id))
            elif payment_method.payment_type == 'PayPal':
                # Redirect to PayPal payment page
                return redirect(url_for('payment.paypal_payment', booking_id=booking_id,
                                      payment_method_id=payment_method.id))
            else:
                flash('Payment method not supported yet', 'warning')
                
        except Exception as e:
            flash(f'Error processing payment: {str(e)}', 'danger')
    
    return render_template('payment/process.html', form=form, booking=booking)

@bp.route('/upi/<int:booking_id>/<int:payment_method_id>', methods=['GET', 'POST'])
@login_required
@require_payment_security
def upi_payment(booking_id, payment_method_id):
    """Process UPI payment"""
    # Get booking and payment method
    booking = Booking.query.get_or_404(booking_id)
    payment_method = PaymentMethod.query.get_or_404(payment_method_id)
    
    # Check ownership
    if booking.student_id != current_user.id or payment_method.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('student.dashboard'))
    
    form = UPIPaymentForm()
    form.upi_id.data = payment_method.method_details
    form.amount.data = booking.amount
    
    if form.validate_on_submit():
        try:
            # Validate UPI ID
            valid, error = PaymentSecurity.validate_upi_id(form.upi_id.data)
            if not valid:
                flash(error, 'danger')
                return render_template('payment/upi.html', form=form, booking=booking)
            
            # Validate payment amount
            valid, error = PaymentSecurity.validate_amount(form.amount.data)
            if not valid:
                flash(error, 'danger')
                return render_template('payment/upi.html', form=form, booking=booking)
            
            # Create UPI payment
            payment = create_upi_payment(
                user_id=current_user.id,
                booking_id=booking_id,
                upi_id=form.upi_id.data,
                amount=float(form.amount.data),
                description=form.description.data
            )
            
            # Create Razorpay order
            order = upi_service.create_upi_order(
                amount=float(form.amount.data),
                currency='INR',
                description=form.description.data,
                booking_id=booking_id,
                user_id=current_user.id
            )
            
            # Generate QR code
            qr_data = upi_service.generate_upi_qr_code(
                upi_id=form.upi_id.data,
                amount=float(form.amount.data),
                description=form.description.data,
                order_id=order['id']
            )
            
            return render_template('payment/upi_qr.html', 
                                  booking=booking,
                                  payment=payment,
                                  order=order,
                                  qr_data=qr_data)
            
        except Exception as e:
            flash(f'Error processing UPI payment: {str(e)}', 'danger')
    
    return render_template('payment/upi.html', form=form, booking=booking)

@bp.route('/paypal/<int:booking_id>/<int:payment_method_id>', methods=['GET', 'POST'])
@login_required
@require_payment_security
def paypal_payment(booking_id, payment_method_id):
    """Process PayPal payment"""
    # Get booking and payment method
    booking = Booking.query.get_or_404(booking_id)
    payment_method = PaymentMethod.query.get_or_404(payment_method_id)
    
    # Check ownership
    if booking.student_id != current_user.id or payment_method.user_id != current_user.id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('student.dashboard'))
    
    form = PayPalPaymentForm()
    form.paypal_email.data = payment_method.method_details
    form.amount.data = booking.amount
    
    if form.validate_on_submit():
        try:
            # Validate PayPal email
            valid, error = PaymentSecurity.validate_paypal_email(form.paypal_email.data)
            if not valid:
                flash(error, 'danger')
                return render_template('payment/paypal.html', form=form, booking=booking)
            
            # Validate payment amount
            valid, error = PaymentSecurity.validate_amount(form.amount.data)
            if not valid:
                flash(error, 'danger')
                return render_template('payment/paypal.html', form=form, booking=booking)
            
            # Create PayPal payment
            payment = create_paypal_payment(
                user_id=current_user.id,
                booking_id=booking_id,
                paypal_email=form.paypal_email.data,
                amount=float(form.amount.data),
                description=form.description.data
            )
            
            # Create PayPal order
            order_data = paypal_service.create_order(
                amount=float(form.amount.data),
                currency='USD',
                description=form.description.data,
                booking_id=booking_id,
                user_id=current_user.id
            )
            
            # Redirect to PayPal for approval
            return redirect(order_data['approval_url'])
            
        except Exception as e:
            flash(f'Error processing PayPal payment: {str(e)}', 'danger')
    
    return render_template('payment/paypal.html', form=form, booking=booking)

@bp.route('/paypal/success')
@login_required
def paypal_success():
    """Handle PayPal payment success"""
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    token = request.args.get('token')
    
    if not payment_id or not payer_id:
        flash('Invalid PayPal response', 'danger')
        return redirect(url_for('payment.index'))
    
    try:
        # Capture the payment
        capture_result = paypal_service.capture_order(payment_id)
        
        if capture_result['status'] == 'success':
            # Find the corresponding payment record
            # This is a simplified approach - in production, you'd want to track the order ID
            flash('Payment completed successfully!', 'success')
            return redirect(url_for('payment.receipt', payment_id=capture_result['payment_id']))
        else:
            flash(f'Payment failed: {capture_result["error"]}', 'danger')
            return redirect(url_for('payment.index'))
            
    except Exception as e:
        flash(f'Error processing PayPal payment: {str(e)}', 'danger')
        return redirect(url_for('payment.index'))

@bp.route('/paypal/cancel')
@login_required
def paypal_cancel():
    """Handle PayPal payment cancellation"""
    flash('Payment was cancelled', 'info')
    return redirect(url_for('payment.index'))

@bp.route('/upi/verify', methods=['POST'])
@login_required
@require_payment_security
def verify_upi_payment():
    """Verify UPI payment status"""
    payment_id = request.json.get('payment_id')
    razorpay_payment_id = request.json.get('razorpay_payment_id')
    razorpay_order_id = request.json.get('razorpay_order_id')
    
    if not all([payment_id, razorpay_payment_id, razorpay_order_id]):
        return jsonify({'status': 'error', 'message': 'Missing required parameters'})
    
    try:
        # Verify payment with Razorpay
        verification = upi_service.verify_upi_payment(razorpay_payment_id, razorpay_order_id)
        
        if verification['status'] == 'success':
            # Process successful payment
            payment = process_upi_payment_success(payment_id, razorpay_payment_id, razorpay_order_id)
            return jsonify({'status': 'success', 'message': 'Payment verified successfully'})
        else:
            # Process failed payment
            process_upi_payment_failure(payment_id, verification['error'])
            return jsonify({'status': 'failed', 'message': verification['error']})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@bp.route('/history')
@login_required
def payment_history():
    """View payment history"""
    form = PaymentSearchForm()
    payments_query = db.session.query(Payment).join(Booking)
    
    # Filter based on user role
    if current_user.role == 'tutor':
        payments_query = payments_query.filter(Booking.tutor_id == current_user.tutor_profile.id)
    else:
        payments_query = payments_query.filter(Booking.student_id == current_user.id)
    
    # Apply filters
    if request.args.get('status'):
        payments_query = payments_query.filter(Payment.status == request.args.get('status'))
    
    if request.args.get('payment_method'):
        payments_query = payments_query.join(PaymentMethod).filter(
            PaymentMethod.payment_type == request.args.get('payment_method')
        )
    
    # Order by creation date
    payments = payments_query.order_by(Payment.created_at.desc()).limit(50).all()
    
    return render_template('payment/history.html', payments=payments, form=form)

@bp.route('/receipt/<payment_id>')
@login_required
def receipt(payment_id):
    """View payment receipt"""
    payment = db.session.query(Payment).join(Booking).filter(
        Payment.gateway_transaction_id == payment_id
    ).first_or_404()
    
    # Check ownership
    if current_user.role == 'tutor':
        if payment.booking.tutor_id != current_user.tutor_profile.id:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('payment.payment_history'))
    else:
        if payment.booking.student_id != current_user.id:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('payment.payment_history'))
    
    return render_template('payment/receipt.html', payment=payment)

@bp.route('/refund/<int:payment_id>', methods=['GET', 'POST'])
@login_required
@require_payment_security
def refund_payment(payment_id):
    """Process payment refund"""
    payment = Payment.query.get_or_404(payment_id)
    
    # Check ownership and permissions
    if current_user.role == 'tutor':
        if payment.booking.tutor_id != current_user.tutor_profile.id:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('payment.payment_history'))
    elif current_user.role != 'admin':
        if payment.booking.student_id != current_user.id:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('payment.payment_history'))
    
    # Check if payment can be refunded
    if payment.status != 'Completed':
        flash('Only completed payments can be refunded', 'warning')
        return redirect(url_for('payment.receipt', payment_id=payment.gateway_transaction_id))
    
    form = RefundForm()
    form.payment_id.data = payment_id
    form.refund_amount.data = payment.amount
    
    if form.validate_on_submit():
        try:
            # Validate refund request
            valid, error = PaymentSecurity.validate_refund_request(
                payment,
                float(form.refund_amount.data),
                form.refund_reason.data
            )
            if not valid:
                flash(error, 'danger')
                return render_template('payment/refund.html', form=form, payment=payment)
            
            # Additional rate limiting check
            user_id = getattr(request, 'user_id', None)
            if user_id:
                valid, error = PaymentSecurity.rate_limit_check(user_id, 'refund')
                if not valid:
                    flash(error, 'danger')
                    return render_template('payment/refund.html', form=form, payment=payment)
            
            # Process refund based on payment gateway
            if payment.payment_gateway == 'PayPal':
                refund_result = paypal_service.process_refund(
                    payment.gateway_transaction_id,
                    float(form.refund_amount.data)
                )
            elif payment.payment_gateway == 'Razorpay':
                refund_result = upi_service.process_upi_refund(
                    payment.gateway_transaction_id,
                    float(form.refund_amount.data)
                )
            else:
                flash('Refund not supported for this payment method', 'warning')
                return redirect(url_for('payment.receipt', payment_id=payment.gateway_transaction_id))
            
            if refund_result['status'] == 'success':
                # Update payment status
                payment.status = 'Refunded'
                
                # Create refund transaction
                refund_transaction = Transaction(
                    payment_id=payment.id,
                    amount=float(form.refund_amount.data),
                    currency=payment.currency,
                    transaction_type='Refund',
                    description=form.refund_reason.data,
                    status='Completed',
                    reference_id=refund_result.get('refund_id')
                )
                db.session.add(refund_transaction)
                db.session.commit()
                
                flash('Refund processed successfully!', 'success')
                return redirect(url_for('payment.receipt', payment_id=payment.gateway_transaction_id))
            else:
                flash(f'Refund failed: {refund_result["error"]}', 'danger')
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing refund: {str(e)}', 'danger')
    
    return render_template('payment/refund.html', form=form, payment=payment)

# Payout routes
@bp.route('/payouts')
@login_required
@role_required('tutor', 'admin')
def payouts():
    """View payouts"""
    if current_user.role == 'tutor':
        payouts = payout_service.get_tutor_payouts(current_user.tutor_profile.id)
    else:
        payouts = payout_service.get_all_payouts()
    
    return render_template('payment/payouts.html', payouts=payouts)

@bp.route('/payouts/request', methods=['GET', 'POST'])
@login_required
@role_required('tutor')
@require_payment_security
def request_payout():
    """Request a payout"""
    form = PayoutRequestForm()
    
    if form.validate_on_submit():
        try:
            # Validate payout amount
            valid, error = PaymentSecurity.validate_amount(form.amount.data)
            if not valid:
                flash(error, 'danger')
                return render_template('payment/request_payout.html', form=form)
            
            # Additional payout method validation
            if form.payout_method.data == 'Bank Transfer':
                # Parse bank details from payout_details
                details = form.payout_details.data.split('|')
                if len(details) >= 2:
                    account_number = details[1] if len(details) > 1 else ''
                    valid, error = PaymentSecurity.validate_bank_account(account_number)
                    if not valid:
                        flash(error, 'danger')
                        return render_template('payment/request_payout.html', form=form)
            elif form.payout_method.data == 'UPI':
                # Parse UPI details from payout_details
                details = form.payout_details.data.split('|')
                if len(details) >= 2:
                    upi_id = details[1] if len(details) > 1 else ''
                    valid, error = PaymentSecurity.validate_upi_id(upi_id)
                    if not valid:
                        flash(error, 'danger')
                        return render_template('payment/request_payout.html', form=form)
            
            payout = payout_service.create_payout_request(
                tutor_id=current_user.tutor_profile.id,
                amount=float(form.amount.data),
                payout_method=form.payout_method.data,
                payout_details=form.payout_details.data,
                notes=form.notes.data
            )
            
            flash('Payout request submitted successfully!', 'success')
            return redirect(url_for('payment.payouts'))
            
        except Exception as e:
            flash(f'Error submitting payout request: {str(e)}', 'danger')
    
    return render_template('payment/request_payout.html', form=form)

@bp.route('/payouts/methods', methods=['GET', 'POST'])
@login_required
@role_required('tutor')
def payout_methods():
    """Manage payout methods"""
    form = PayoutMethodForm()
    
    if form.validate_on_submit():
        try:
            payout_method = create_payout_method(
                tutor_id=current_user.tutor_profile.id,
                method_type=form.method_type.data,
                account_holder_name=form.account_holder_name.data,
                account_details=form.account_details.data,
                bank_name=form.bank_name.data,
                ifsc_code=form.ifsc_code.data
            )
            
            flash('Payout method added successfully!', 'success')
            return redirect(url_for('payment.payout_methods'))
            
        except Exception as e:
            flash(f'Error adding payout method: {str(e)}', 'danger')
    
    # Get existing payout methods
    methods = get_tutor_payout_methods(current_user.tutor_profile.id)
    
    return render_template('payment/payout_methods.html', form=form, methods=methods)

# Analytics routes
@bp.route('/analytics')
@login_required
@role_required('admin')
def analytics():
    """Payment analytics dashboard"""
    form = AnalyticsFilterForm()
    
    # Get filter parameters
    period = request.args.get('period', '30')
    payment_method = request.args.get('payment_method', '')
    currency = request.args.get('currency', '')
    
    # Calculate date range
    days = int(period)
    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()
    
    # Get analytics data
    revenue_summary = payment_analytics.get_revenue_summary(start_date, end_date, currency or None)
    payment_method_analytics = payment_analytics.get_payment_method_analytics(start_date, end_date)
    monthly_revenue = payment_analytics.get_monthly_revenue()
    top_tutors = payment_analytics.get_top_tutors_by_earnings(10, start_date, end_date)
    
    return render_template('payment/analytics.html',
                          form=form,
                          revenue_summary=revenue_summary,
                          payment_method_analytics=payment_method_analytics,
                          monthly_revenue=monthly_revenue,
                          top_tutors=top_tutors)

@bp.route('/export/<format>')
@login_required
@role_required('admin')
def export_data(format):
    """Export payment data"""
    try:
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')
        
        # Parse dates
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Export data
        data = payment_analytics.export_payment_data(format, start_date, end_date, status)
        
        if data:
            # Create file for download
            output = io.BytesIO()
            output.write(data.encode('utf-8'))
            output.seek(0)
            
            filename = f"payment_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            
            return send_file(
                output,
                as_attachment=True,
                download_name=filename,
                mimetype='text/csv' if format == 'csv' else 'application/json'
            )
        else:
            flash('No data available for export', 'warning')
            return redirect(url_for('payment.analytics'))
            
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'danger')
        return redirect(url_for('payment.analytics'))