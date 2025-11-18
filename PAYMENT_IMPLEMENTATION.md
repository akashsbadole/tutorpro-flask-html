# Payment System Implementation

This document provides a comprehensive overview of the payment system implementation for TutorPro, including UPI and PayPal integration, tutor payouts, and payment analytics.

## Overview

The payment system is designed to handle secure online transactions for tutoring services through multiple payment gateways, with support for UPI (via Razorpay) and PayPal. The system includes:

- Multiple payment method support (UPI, PayPal, Credit/Debit Cards)
- Secure payment processing with fraud detection
- Tutor payout management
- Comprehensive payment analytics
- Refund processing
- Audit logging for all transactions

## Architecture

### Components

1. **Payment Models** (`app/models/payment.py`)
   - `PaymentMethod`: Stores user payment methods
   - `Payment`: Tracks all payment transactions
   - `Transaction`: Detailed payment records
   - `Payout`: Tutor payout requests and processing

2. **Payment Services**
   - `UPIService` (`app/payment/upi.py`): Handles UPI payments via Razorpay
   - `PayPalService` (`app/payment/paypal.py`): Handles PayPal payments
   - `PayoutService` (`app/payment/payouts.py`): Manages tutor payouts
   - `PaymentAnalytics` (`app/payment/analytics.py`): Provides payment analytics
   - `PaymentSecurity` (`app/payment/security.py`): Security and validation utilities

3. **Payment Routes** (`app/payment/routes.py`)
   - Web routes for payment processing
   - Integration with payment gateways
   - Refund processing
   - Payout management

4. **Payment API** (`app/api/payment.py`)
   - RESTful API endpoints
   - Webhook handling
   - Rate limiting and security

5. **Payment Templates** (`app/templates/payment/`)
   - User interface for payment processing
   - Payment history and receipts
   - Payout management interface

## Payment Flow

### 1. Payment Method Selection
- Users can add multiple payment methods (UPI, PayPal, Cards)
- Default payment method can be set
- Payment methods are validated and stored securely

### 2. Payment Processing
- User selects payment method for a booking
- System redirects to appropriate payment gateway
- Payment is processed securely with fraud detection

### 3. Payment Confirmation
- Webhooks confirm successful payments
- Payment status is updated in database
- Receipt is generated and sent to user

### 4. Refund Processing
- Refunds can be requested within policy period
- Refunds are processed through original payment gateway
- Refund transactions are tracked

## UPI Payment Integration

### Features
- QR code generation for UPI payments
- Real-time payment verification
- Support for all major UPI apps
- Automatic payment status updates

### Implementation Details
- Uses Razorpay SDK for UPI processing
- QR codes generated using `qrcode` library
- Payment verification through webhooks
- Automatic retry for failed payments

## PayPal Payment Integration

### Features
- PayPal checkout integration
- Support for one-time and recurring payments
- Webhook-based payment confirmation
- Subscription management

### Implementation Details
- Uses PayPal Checkout SDK
- Order creation and capture flow
- Webhook handling for payment events
- Refund processing through PayPal API

## Security Features

### 1. Input Validation
- Payment amount validation
- UPI ID format validation
- PayPal email validation
- Card number validation (Luhn algorithm)
- Bank account validation

### 2. Fraud Detection
- Unusual amount detection
- Rapid transaction detection
- Geographic validation
- Pattern analysis

### 3. Rate Limiting
- Payment attempt limits
- Refund request limits
- API endpoint rate limiting
- Time-based restrictions

### 4. Data Protection
- Encrypted storage of sensitive data
- Secure transmission to payment gateways
- PCI compliance considerations
- Audit logging

## Tutor Payout System

### Features
- Multiple payout methods (Bank Transfer, UPI, PayPal)
- Payout request management
- Automatic processing scheduling
- Payout history tracking

### Implementation Details
- Payout requests with validation
- Integration with payment gateways for payouts
- Status tracking and notifications
- Tax calculation and reporting

## Payment Analytics

### Features
- Revenue tracking and reporting
- Payment method analytics
- Transaction trends
- Export functionality
- Real-time dashboards

### Implementation Details
- Database aggregation queries
- Chart.js integration for visualization
- Filterable data views
- CSV/JSON export options

## Configuration

### Environment Variables
```
# PayPal Configuration
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
PAYPAL_ENVIRONMENT=sandbox

# Razorpay Configuration
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Payment Settings
PAYMENT_CURRENCY=USD
PAYMENT_TIMEOUT_MINUTES=30
REFUND_POLICY_DAYS=7
PAYOUT_PROCESSING_DAYS=3
```

### Security Configuration
```
# Fraud Detection
FRAUD_MAX_AMOUNT=5000.00
ALLOWED_COUNTRIES=US,CA,GB,IN

# Rate Limiting
RATE_LIMIT_PAYMENT=10
RATE_LIMIT_PAYMENT_WINDOW=3600
RATE_LIMIT_REFUND=5
RATE_LIMIT_REFUND_WINDOW=3600
```

## API Endpoints

### Payment Processing
- `POST /api/payment/methods` - Add payment method
- `POST /api/payment/upi/order` - Create UPI order
- `POST /api/payment/paypal/order` - Create PayPal order
- `POST /api/payment/refund` - Process refund

### Payout Management
- `GET /api/payment/payouts` - Get payout history
- `POST /api/payment/payouts` - Request payout
- `GET /api/payment/payouts/{id}` - Get payout details

### Analytics
- `GET /api/payment/analytics/revenue` - Get revenue analytics
- `GET /api/payment/analytics/methods` - Get payment method analytics
- `GET /api/payment/export` - Export payment data

### Webhooks
- `POST /api/payment/webhooks/paypal` - PayPal webhook handler
- `POST /api/payment/webhooks/razorpay` - Razorpay webhook handler

## Database Schema

### Payment Methods Table
```sql
CREATE TABLE payment_methods (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    payment_type ENUM('UPI', 'PayPal', 'Credit Card', 'Debit Card') NOT NULL,
    method_details VARCHAR(255) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Payments Table
```sql
CREATE TABLE payments (
    id INTEGER PRIMARY KEY,
    booking_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    payment_method_id INTEGER NOT NULL,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    status ENUM('Pending', 'Completed', 'Failed', 'Refunded') DEFAULT 'Pending',
    payment_gateway VARCHAR(50) NOT NULL,
    gateway_transaction_id VARCHAR(100),
    failure_reason TEXT,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id),
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id)
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    payment_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    transaction_type ENUM('Payment', 'Refund', 'Payout') NOT NULL,
    description TEXT NOT NULL,
    status ENUM('Pending', 'Completed', 'Failed') DEFAULT 'Pending',
    reference_id VARCHAR(100),
    gateway_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (payment_id) REFERENCES payments(id)
);
```

### Payouts Table
```sql
CREATE TABLE payouts (
    id INTEGER PRIMARY KEY,
    tutor_id INTEGER NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    payout_method ENUM('Bank Transfer', 'UPI', 'PayPal') NOT NULL,
    payout_details VARCHAR(255) NOT NULL,
    status ENUM('Pending', 'Processing', 'Completed', 'Failed') DEFAULT 'Pending',
    reference_id VARCHAR(100),
    failure_reason TEXT,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (tutor_id) REFERENCES tutor_profiles(id)
);
```

## Error Handling

### Payment Errors
- Invalid payment method
- Insufficient funds
- Payment gateway errors
- Network timeouts
- Fraud detection triggers

### Refund Errors
- Refund period expired
- Invalid refund amount
- Refund already processed
- Gateway refund errors

### Payout Errors
- Invalid payout method
- Insufficient balance
- Bank transfer failures
- Invalid account details

## Testing

### UPI Payment Testing
1. Use Razorpay test mode
2. Test with test UPI IDs
3. Verify QR code generation
4. Test payment verification flow

### PayPal Payment Testing
1. Use PayPal sandbox
2. Test with sandbox accounts
3. Verify order creation and capture
4. Test webhook handling

### Security Testing
1. Test input validation
2. Test fraud detection
3. Test rate limiting
4. Test webhook security

## Deployment

### Production Checklist
- [ ] Update payment gateway credentials
- [ ] Configure webhook endpoints
- [ ] Set production URLs
- [ ] Enable SSL certificates
- [ ] Configure monitoring
- [ ] Set up backup systems
- [ ] Test end-to-end flow

## Monitoring and Maintenance

### Key Metrics
- Payment success rate
- Transaction processing time
- Fraud detection rate
- Payout processing time
- Revenue tracking

### Regular Tasks
- Monitor webhook failures
- Review fraud detection rules
- Update payment gateway SDKs
- Analyze payment trends
- Optimize database queries

## Compliance

### PCI DSS
- No storage of full card details
- Encrypted transmission of data
- Access control measures
- Regular security audits

### Data Protection
- GDPR compliance for EU users
- Data retention policies
- User consent management
- Secure data deletion

## Future Enhancements

### Planned Features
- Additional payment gateways (Stripe, Apple Pay)
- Cryptocurrency payments
- Advanced fraud detection with ML
- Subscription management
- Multi-currency support
- Mobile payment optimization

## Support

### Troubleshooting
1. Check payment gateway status
2. Verify webhook configuration
3. Review error logs
4. Validate API credentials
5. Test with small amounts

### Contact Information
- Payment Issues: payments@tutorpro.com
- Technical Support: support@tutorpro.com
- Documentation: https://docs.tutorpro.com/payments