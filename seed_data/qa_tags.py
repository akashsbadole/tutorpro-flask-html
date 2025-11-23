"""
Seed data for Q&A system tags
"""
from datetime import datetime
from app.models.qa_system import Tag

def create_qa_tags():
    """Create default Q&A tags"""
    
    tags = [
        {
            'name': 'Mathematics',
            'description': 'Questions related to mathematics topics',
            'color': '#3498DB',
            'icon': 'fa-calculator'
        },
        {
            'name': 'Physics',
            'description': 'Questions about physics concepts and problems',
            'color': '#E74C3C',
            'icon': 'fa-atom'
        },
        {
            'name': 'Chemistry',
            'description': 'Chemistry-related questions and answers',
            'color': '#27AE60',
            'icon': 'fa-flask'
        },
        {
            'name': 'Biology',
            'description': 'Biology and life sciences questions',
            'color': '#16A085',
            'icon': 'fa-dna'
        },
        {
            'name': 'Computer Science',
            'description': 'Programming and computer science questions',
            'color': '#2C3E50',
            'icon': 'fa-laptop-code'
        },
        {
            'name': 'Programming',
            'description': 'Programming language specific questions',
            'color': '#8E44AD',
            'icon': 'fa-code'
        },
        {
            'name': 'Web Development',
            'description': 'HTML, CSS, JavaScript, and web frameworks',
            'color': '#F39C12',
            'icon': 'fa-globe'
        },
        {
            'name': 'Data Structures',
            'description': 'Questions about data structures and algorithms',
            'color': '#34495E',
            'icon': 'fa-sitemap'
        },
        {
            'name': 'Databases',
            'description': 'Database design and SQL questions',
            'color': '#1ABC9C',
            'icon': 'fa-database'
        },
        {
            'name': 'Machine Learning',
            'description': 'ML and AI related questions',
            'color': '#E67E22',
            'icon': 'fa-robot'
        },
        {
            'name': 'English',
            'description': 'English language and literature questions',
            'color': '#9B59B6',
            'icon': 'fa-book'
        },
        {
            'name': 'History',
            'description': 'Historical questions and discussions',
            'color': '#D35400',
            'icon': 'fa-landmark'
        },
        {
            'name': 'Geography',
            'description': 'Geography and earth science questions',
            'color': '#2980B9',
            'icon': 'fa-map-marked-alt'
        },
        {
            'name': 'Economics',
            'description': 'Economic theory and applications',
            'color': '#27AE60',
            'icon': 'fa-chart-line'
        },
        {
            'name': 'Business',
            'description': 'Business and entrepreneurship questions',
            'color': '#F39C12',
            'icon': 'fa-briefcase'
        },
        {
            'name': 'Accounting',
            'description': 'Accounting and finance questions',
            'color': '#16A085',
            'icon': 'fa-calculator'
        },
        {
            'name': 'Statistics',
            'description': 'Statistical analysis and probability',
            'color': '#8E44AD',
            'icon': 'fa-chart-bar'
        },
        {
            'name': 'Calculus',
            'description': 'Calculus and advanced mathematics',
            'color': '#C0392B',
            'icon': 'fa-square-root-alt'
        },
        {
            'name': 'Algebra',
            'description': 'Algebra and linear algebra questions',
            'color': '#2980B9',
            'icon': 'fa-superscript'
        },
        {
            'name': 'Geometry',
            'description': 'Geometry and trigonometry questions',
            'color': '#27AE60',
            'icon': 'fa-shapes'
        },
        {
            'name': 'Exam Preparation',
            'description': 'Questions about exam preparation strategies',
            'color': '#E74C3C',
            'icon': 'fa-graduation-cap'
        },
        {
            'name': 'Homework Help',
            'description': 'General homework assistance questions',
            'color': '#F39C12',
            'icon': 'fa-pencil-alt'
        },
        {
            'name': 'Study Tips',
            'description': 'Study techniques and learning strategies',
            'color': '#3498DB',
            'icon': 'fa-lightbulb'
        },
        {
            'name': 'Career Guidance',
            'description': 'Career advice and professional development',
            'color': '#9B59B6',
            'icon': 'fa-compass'
        },
        {
            'name': 'Concept Clarification',
            'description': 'Questions seeking clarification of concepts',
            'color': '#1ABC9C',
            'icon': 'fa-question-circle'
        },
        {
            'name': 'Problem Solving',
            'description': 'Step-by-step problem solving help',
            'color': '#E67E22',
            'icon': 'fa-puzzle-piece'
        },
        {
            'name': 'Theory',
            'description': 'Theoretical concepts and explanations',
            'color': '#34495E',
            'icon': 'fa-brain'
        },
        {
            'name': 'Practical',
            'description': 'Practical applications and examples',
            'color': '#16A085',
            'icon': 'fa-cogs'
        },
        {
            'name': 'Beginner',
            'description': 'Questions suitable for beginners',
            'color': '#27AE60',
            'icon': 'fa-seedling'
        },
        {
            'name': 'Intermediate',
            'description': 'Intermediate level questions',
            'color': '#F39C12',
            'icon': 'fa-layer-group'
        },
        {
            'name': 'Advanced',
            'description': 'Advanced level questions',
            'color': '#E74C3C',
            'icon': 'fa-mountain'
        },
        {
            'name': 'Quick Help',
            'description': 'Questions needing quick assistance',
            'color': '#3498DB',
            'icon': 'fa-bolt'
        },
        {
            'name': 'Detailed Explanation',
            'description': 'Questions requiring detailed explanations',
            'color': '#9B59B6',
            'icon': 'fa-book-open'
        },
        {
            'name': 'Examples',
            'description': 'Questions requesting examples',
            'color': '#1ABC9C',
            'icon': 'fa-list-ol'
        },
        {
            'name': 'Resources',
            'description': 'Questions about learning resources',
            'color': '#E67E22',
            'icon': 'fa-link'
        },
        {
            'name': 'Online Learning',
            'description': 'Online learning related questions',
            'color': '#34495E',
            'icon': 'fa-laptop'
        },
        {
            'name': 'Study Group',
            'description': 'Study group and collaboration questions',
            'color': '#16A085',
            'icon': 'fa-users'
        },
        {
            'name': 'Time Management',
            'description': 'Time management and productivity',
            'color': '#F39C12',
            'icon': 'fa-clock'
        },
        {
            'name': 'Motivation',
            'description': 'Motivation and study mindset',
            'color': '#E74C3C',
            'icon': 'fa-heart'
        },
        {
            'name': 'Test Taking',
            'description': 'Test taking strategies and techniques',
            'color': '#3498DB',
            'icon': 'fa-clipboard-check'
        },
        {
            'name': 'Note Taking',
            'description': 'Effective note taking methods',
            'color': '#27AE60',
            'icon': 'fa-sticky-note'
        },
        {
            'name': 'Research',
            'description': 'Research methods and techniques',
            'color': '#9B59B6',
            'icon': 'fa-search'
        },
        {
            'name': 'Writing',
            'description': 'Academic writing and composition',
            'color': '#E67E22',
            'icon': 'fa-pen-fancy'
        },
        {
            'name': 'Presentation',
            'description': 'Presentation skills and public speaking',
            'color': '#34495E',
            'icon': 'fa-presentation'
        },
        {
            'name': 'Project Help',
            'description': 'Project assistance and guidance',
            'color': '#16A085',
            'icon': 'fa-project-diagram'
        },
        {
            'name': 'Internship',
            'description': 'Internship and work experience questions',
            'color': '#F39C12',
            'icon': 'fa-briefcase'
        },
        {
            'name': 'Resume',
            'description': 'Resume writing and job applications',
            'color': '#E74C3C',
            'icon': 'fa-file-alt'
        },
        {
            'name': 'Interview',
            'description': 'Interview preparation and tips',
            'color': '#3498DB',
            'icon': 'fa-comments'
        },
        {
            'name': 'Networking',
            'description': 'Professional networking advice',
            'color': '#27AE60',
            'icon': 'fa-network-wired'
        },
        {
            'name': 'Skills Development',
            'description': 'Professional skills development',
            'color': '#9B59B6',
            'icon': 'fa-chart-line'
        }
    ]
    
    created_tags = []
    for tag_data in tags:
        tag = Tag(
            **tag_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        created_tags.append(tag)
    
    return created_tags

if __name__ == '__main__':
    from app import create_app, db
    
    app = create_app()
    with app.app_context():
        # Check if tags already exist
        existing_count = Tag.query.count()
        if existing_count == 0:
            tags = create_qa_tags()
            for tag in tags:
                db.session.add(tag)
            db.session.commit()
            print(f"Created {len(tags)} Q&A tags")
        else:
            print(f"Q&A tags already exist ({existing_count} found)")