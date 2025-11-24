"""
Advanced Analytics API Endpoints
Provides RESTful API for advanced analytics and business intelligence
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.advanced_analytics import AdvancedAnalytics
from app.utils.decorators import admin_required
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('analytics_api', __name__, url_prefix='/api/analytics')

# Initialize analytics service
analytics_service = AdvancedAnalytics()

@bp.route('/dashboard', methods=['GET'])
@login_required
@admin_required
def get_bi_dashboard():
    """Get comprehensive business intelligence dashboard"""
    try:
        # Get date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use ISO format (YYYY-MM-DD)'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use ISO format (YYYY-MM-DD)'}), 400
        
        # Get dashboard data
        dashboard_data = analytics_service.get_business_intelligence_dashboard(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting BI dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve dashboard data'
        }), 500

@bp.route('/revenue/forecast', methods=['GET'])
@login_required
@admin_required
def get_revenue_forecast():
    """Get revenue forecast"""
    try:
        # Get parameters
        days_ahead = int(request.args.get('days_ahead', 30))
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Get forecast
        forecast_data = analytics_service.prediction_models['revenue_forecast'].predict(
            start_date, end_date, days_ahead
        )
        
        return jsonify({
            'success': True,
            'data': forecast_data
        })
        
    except Exception as e:
        logger.error(f"Error getting revenue forecast: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate revenue forecast'
        }), 500

@bp.route('/revenue/trends', methods=['GET'])
@login_required
@admin_required
def get_revenue_trends():
    """Get revenue trends analysis"""
    try:
        # Get date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get trends data
        trends_data = analytics_service._analyze_revenue_trends(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': trends_data
        })
        
    except Exception as e:
        logger.error(f"Error getting revenue trends: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze revenue trends'
        }), 500

@bp.route('/users/acquisition', methods=['GET'])
@login_required
@admin_required
def get_user_acquisition():
    """Get user acquisition analytics"""
    try:
        # Get date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get acquisition data
        acquisition_data = analytics_service._analyze_user_acquisition(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': acquisition_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user acquisition: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze user acquisition'
        }), 500

@bp.route('/users/engagement', methods=['GET'])
@login_required
@admin_required
def get_user_engagement():
    """Get user engagement analytics"""
    try:
        # Get date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get engagement data
        engagement_data = analytics_service._analyze_user_engagement(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': engagement_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user engagement: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze user engagement'
        }), 500

@bp.route('/users/retention', methods=['GET'])
@login_required
@admin_required
def get_user_retention():
    """Get user retention analytics"""
    try:
        # Get date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get retention data
        retention_data = analytics_service._analyze_user_retention(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': retention_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user retention: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze user retention'
        }), 500

@bp.route('/users/lifetime-value', methods=['GET'])
@login_required
@admin_required
def get_customer_lifetime_value():
    """Get customer lifetime value analytics"""
    try:
        # Get LTV data
        ltv_data = analytics_service._calculate_customer_lifetime_value()
        
        return jsonify({
            'success': True,
            'data': ltv_data
        })
        
    except Exception as e:
        logger.error(f"Error getting customer lifetime value: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to calculate customer lifetime value'
        }), 500

@bp.route('/market/subjects', methods=['GET'])
@login_required
@admin_required
def get_subject_demand():
    """Get subject demand analytics"""
    try:
        # Get date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get subject demand data
        subject_data = analytics_service._analyze_subject_demand(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': subject_data
        })
        
    except Exception as e:
        logger.error(f"Error getting subject demand: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze subject demand'
        }), 500

@bp.route('/market/geographic', methods=['GET'])
@login_required
@admin_required
def get_geographic_distribution():
    """Get geographic distribution analytics"""
    try:
        # Get date parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get geographic data
        geographic_data = analytics_service._analyze_geographic_distribution(start_date, end_date)
        
        return jsonify({
            'success': True,
            'data': geographic_data
        })
        
    except Exception as e:
        logger.error(f"Error getting geographic distribution: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze geographic distribution'
        }), 500

@bp.route('/tutors/performance', methods=['GET'])
@login_required
@admin_required
def get_tutor_performance():
    """Get tutor performance analytics"""
    try:
        # Get performance data
        performance_data = analytics_service.prediction_models['tutor_performance'].analyze_performance()
        
        return jsonify({
            'success': True,
            'data': performance_data
        })
        
    except Exception as e:
        logger.error(f"Error getting tutor performance: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to analyze tutor performance'
        }), 500

@bp.route('/tutors/underperforming', methods=['GET'])
@login_required
@admin_required
def get_underperforming_tutors():
    """Get underperforming tutors"""
    try:
        # Get underperforming tutors
        underperforming_data = analytics_service.prediction_models['tutor_performance'].identify_underperforming()
        
        return jsonify({
            'success': True,
            'data': underperforming_data
        })
        
    except Exception as e:
        logger.error(f"Error getting underperforming tutors: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to identify underperforming tutors'
        }), 500

@bp.route('/courses/completion', methods=['GET'])
@login_required
@admin_required
def get_course_completion():
    """Get course completion predictions"""
    try:
        # Get completion data
        completion_data = analytics_service.prediction_models['course_completion'].predict_completion_rates()
        
        return jsonify({
            'success': True,
            'data': completion_data
        })
        
    except Exception as e:
        logger.error(f"Error getting course completion: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to predict course completion rates'
        }), 500

@bp.route('/churn/prediction', methods=['GET'])
@login_required
@admin_required
def get_churn_prediction():
    """Get user churn prediction"""
    try:
        # Get churn risk data
        churn_data = analytics_service.prediction_models['user_churn'].predict_churn_risk()
        
        return jsonify({
            'success': True,
            'data': churn_data
        })
        
    except Exception as e:
        logger.error(f"Error getting churn prediction: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to predict user churn'
        }), 500

@bp.route('/churn/high-risk', methods=['GET'])
@login_required
@admin_required
def get_high_risk_users():
    """Get high-risk users for churn"""
    try:
        # Get high-risk users
        high_risk_data = analytics_service.prediction_models['user_churn'].identify_high_risk_users()
        
        return jsonify({
            'success': True,
            'data': high_risk_data
        })
        
    except Exception as e:
        logger.error(f"Error getting high-risk users: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to identify high-risk users'
        }), 500

@bp.route('/predictive/insights', methods=['GET'])
@login_required
@admin_required
def get_predictive_insights():
    """Get predictive insights and recommendations"""
    try:
        # Get predictive insights
        insights_data = analytics_service._get_predictive_insights()
        
        return jsonify({
            'success': True,
            'data': insights_data
        })
        
    except Exception as e:
        logger.error(f"Error getting predictive insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate predictive insights'
        }), 500

@bp.route('/export', methods=['GET'])
@login_required
@admin_required
def export_analytics():
    """Export analytics data in various formats"""
    try:
        # Get parameters
        export_type = request.args.get('type', 'dashboard')
        format_type = request.args.get('format', 'json')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Parse dates
        start_date = None
        end_date = None
        
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # Set default dates if not provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get data based on export type
        if export_type == 'dashboard':
            data = analytics_service.get_business_intelligence_dashboard(start_date, end_date)
        elif export_type == 'revenue':
            data = analytics_service._get_revenue_intelligence(start_date, end_date)
        elif export_type == 'users':
            data = analytics_service._get_user_intelligence(start_date, end_date)
        elif export_type == 'market':
            data = analytics_service._get_market_intelligence(start_date, end_date)
        else:
            return jsonify({'error': 'Invalid export type'}), 400
        
        # Export in requested format
        if format_type.lower() == 'csv':
            return jsonify({
                'success': True,
                'data': data,
                'format': 'json',  # For now, return JSON
                'message': 'CSV export not implemented yet'
            })
        else:
            return jsonify({
                'success': True,
                'data': data,
                'format': 'json'
            })
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to export analytics data'
        }), 500

@bp.route('/health', methods=['GET'])
def analytics_health_check():
    """Health check for analytics service"""
    try:
        # Test analytics service
        test_data = analytics_service.get_business_intelligence_dashboard(
            datetime.utcnow() - timedelta(days=1),
            datetime.utcnow()
        )
        
        return jsonify({
            'status': 'healthy',
            'service': 'Advanced Analytics',
            'timestamp': datetime.utcnow().isoformat(),
            'data_points': len(test_data) if isinstance(test_data, dict) else 0
        }), 200
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'Advanced Analytics',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500