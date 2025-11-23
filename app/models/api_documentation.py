from datetime import datetime
from app import db

class APIDocumentation(db.Model):
    """
    API documentation for all endpoints
    """
    __tablename__ = 'api_documentation'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # API endpoint details
    endpoint_path = db.Column(db.String(255), nullable=False, index=True)
    http_method = db.Column(db.Enum(
        'GET',
        'POST',
        'PUT',
        'DELETE',
        'PATCH',
        'OPTIONS',
        'HEAD',
        name='http_methods'
    ), nullable=False, index=True)
    
    # Documentation details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(500))
    
    # Request details
    request_parameters = db.Column(db.Text)  # JSON object
    request_headers = db.Column(db.Text)  # JSON object
    request_body_schema = db.Column(db.Text)  # JSON object
    request_example = db.Column(db.Text)  # JSON object
    
    # Response details
    response_schema = db.Column(db.Text)  # JSON object
    response_example = db.Column(db.Text)  # JSON object
    possible_status_codes = db.Column(db.Text)  # JSON object
    
    # Authentication
    authentication_required = db.Column(db.Boolean, default=False)
    authentication_type = db.Column(db.Enum(
        'None',
        'API Key',
        'JWT',
        'OAuth 2.0',
        'Basic Auth',
        name='auth_types'
    ), nullable=False, default='None')
    
    # Rate limiting
    rate_limit = db.Column(db.String(50))  # e.g., "100 per hour"
    
    # Versioning
    api_version = db.Column(db.String(20), nullable=False, default='v1')
    deprecated = db.Column(db.Boolean, default=False)
    deprecation_message = db.Column(db.Text)
    
    # Category and tags
    category = db.Column(db.String(100), nullable=False, index=True)
    tags = db.Column(db.Text)  # JSON array
    
    # Testing
    test_enabled = db.Column(db.Boolean, default=True)
    test_parameters = db.Column(db.Text)  # JSON object
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<APIDocumentation {self.id}: {self.http_method} {self.endpoint_path}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'endpoint_path': self.endpoint_path,
            'http_method': self.http_method,
            'title': self.title,
            'description': self.description,
            'summary': self.summary,
            'request_parameters': self.request_parameters,
            'request_headers': self.request_headers,
            'request_body_schema': self.request_body_schema,
            'request_example': self.request_example,
            'response_schema': self.response_schema,
            'response_example': self.response_example,
            'possible_status_codes': self.possible_status_codes,
            'authentication_required': self.authentication_required,
            'authentication_type': self.authentication_type,
            'rate_limit': self.rate_limit,
            'api_version': self.api_version,
            'deprecated': self.deprecated,
            'deprecation_message': self.deprecation_message,
            'category': self.category,
            'tags': self.tags,
            'test_enabled': self.test_enabled,
            'test_parameters': self.test_parameters,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class APIExample(db.Model):
    """
    Code examples for API usage
    """
    __tablename__ = 'api_examples'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Example details
    api_doc_id = db.Column(db.Integer, db.ForeignKey('api_documentation.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Code example
    programming_language = db.Column(db.Enum(
        'Python',
        'JavaScript',
        'cURL',
        'PHP',
        'Java',
        'C#',
        'Ruby',
        'Go',
        'Swift',
        'Kotlin',
        name='programming_languages'
    ), nullable=False)
    
    code_example = db.Column(db.Text, nullable=False)
    code_syntax_highlighting = db.Column(db.String(50), default='auto')
    
    # Execution details
    is_executable = db.Column(db.Boolean, default=False)
    execution_environment = db.Column(db.Text)  # JSON object
    
    # Response example
    expected_response = db.Column(db.Text)  # JSON object
    
    # Metadata
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    api_documentation = db.relationship('APIDocumentation', backref='examples')
    
    def __repr__(self):
        return f'<APIExample {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'api_doc_id': self.api_doc_id,
            'title': self.title,
            'description': self.description,
            'programming_language': self.programming_language,
            'code_example': self.code_example,
            'code_syntax_highlighting': self.code_syntax_highlighting,
            'is_executable': self.is_executable,
            'execution_environment': self.execution_environment,
            'expected_response': self.expected_response,
            'is_featured': self.is_featured,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class APITestCase(db.Model):
    """
    Test cases for API endpoints
    """
    __tablename__ = 'api_test_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Test case details
    api_doc_id = db.Column(db.Integer, db.ForeignKey('api_documentation.id'), nullable=False)
    test_name = db.Column(db.String(200), nullable=False)
    test_description = db.Column(db.Text)
    
    # Test configuration
    test_type = db.Column(db.Enum(
        'Positive',
        'Negative',
        'Edge Case',
        'Security',
        'Performance',
        name='test_types'
    ), nullable=False)
    
    # Request details
    test_headers = db.Column(db.Text)  # JSON object
    test_parameters = db.Column(db.Text)  # JSON object
    test_body = db.Column(db.Text)  # JSON object
    
    # Expected response
    expected_status_code = db.Column(db.Integer, nullable=False)
    expected_response_body = db.Column(db.Text)  # JSON object
    expected_response_headers = db.Column(db.Text)  # JSON object
    
    # Test execution
    is_automated = db.Column(db.Boolean, default=True)
    test_frequency = db.Column(db.Enum(
        'Once',
        'Hourly',
        'Daily',
        'Weekly',
        'On Deploy',
        name='test_frequencies'
    ), nullable=False, default='Daily')
    
    # Results
    last_run_at = db.Column(db.DateTime)
    last_run_status = db.Column(db.Enum(
        'Not Run',
        'Passed',
        'Failed',
        'Error',
        name='test_statuses'
    ), nullable=False, default='Not Run')
    
    last_run_details = db.Column(db.Text)  # JSON object
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    api_documentation = db.relationship('APIDocumentation', backref='test_cases')
    
    def __repr__(self):
        return f'<APITestCase {self.id}: {self.test_name}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'api_doc_id': self.api_doc_id,
            'test_name': self.test_name,
            'test_description': self.test_description,
            'test_type': self.test_type,
            'test_headers': self.test_headers,
            'test_parameters': self.test_parameters,
            'test_body': self.test_body,
            'expected_status_code': self.expected_status_code,
            'expected_response_body': self.expected_response_body,
            'expected_response_headers': self.expected_response_headers,
            'is_automated': self.is_automated,
            'test_frequency': self.test_frequency,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'last_run_status': self.last_run_status,
            'last_run_details': self.last_run_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class APIChangeLog(db.Model):
    """
    Change log for API updates
    """
    __tablename__ = 'api_change_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Change details
    change_type = db.Column(db.Enum(
        'New Endpoint',
        'Updated Endpoint',
        'Deprecated Endpoint',
        'Removed Endpoint',
        'Breaking Change',
        'Security Update',
        'Performance Improvement',
        name='change_types'
    ), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Affected endpoints
    affected_endpoints = db.Column(db.Text)  # JSON array of endpoint IDs
    
    # Version information
    api_version = db.Column(db.String(20), nullable=False)
    previous_version = db.Column(db.String(20))
    
    # Impact assessment
    impact_level = db.Column(db.Enum(
        'Low',
        'Medium',
        'High',
        'Critical',
        name='impact_levels'
    ), nullable=False)
    
    # Migration guide
    migration_required = db.Column(db.Boolean, default=False)
    migration_guide = db.Column(db.Text)
    
    # Release information
    release_date = db.Column(db.DateTime, nullable=False)
    release_notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<APIChangeLog {self.id}: {self.title}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'change_type': self.change_type,
            'title': self.title,
            'description': self.description,
            'affected_endpoints': self.affected_endpoints,
            'api_version': self.api_version,
            'previous_version': self.previous_version,
            'impact_level': self.impact_level,
            'migration_required': self.migration_required,
            'migration_guide': self.migration_guide,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'release_notes': self.release_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }