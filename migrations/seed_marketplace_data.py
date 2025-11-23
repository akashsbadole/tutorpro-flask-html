"""
Seed data for marketplace categories and subjects
Run this script after migrations to populate initial data
"""

from app import create_app, db
from app.models.category import SubjectCategory, Subject, SubjectLevel, LearningObjective
from app.models.user import User
from app.models.tutor import TutorProfile
from datetime import datetime
import json

def seed_subject_levels():
    """Create subject proficiency levels"""
    levels = [
        {'name': 'Beginner', 'description': 'Just starting out, no prior experience needed', 'sort_order': 1},
        {'name': 'Intermediate', 'description': 'Some experience, looking to improve skills', 'sort_order': 2},
        {'name': 'Advanced', 'description': 'Experienced, seeking mastery', 'sort_order': 3},
        {'name': 'Expert', 'description': 'Professional level, deep expertise', 'sort_order': 4}
    ]
    
    for level_data in levels:
        level = SubjectLevel(**level_data)
        db.session.add(level)
    
    db.session.commit()
    print("✓ Subject levels created")

def seed_academic_categories():
    """Create academic subject categories"""
    
    # Main Academic Category
    academic = SubjectCategory(
        name='Academic Tuition',
        slug='academic-tuition',
        description='Comprehensive academic support for all levels',
        icon_url='/static/icons/academic.svg',
        banner_url='/static/banners/academic.jpg',
        color='#4A90E2',
        sort_order=1,
        is_featured=True,
        meta_title='Academic Tuition - Expert Tutors for All Subjects',
        meta_description='Find expert tutors for mathematics, science, languages, and more. Personalized learning for K-12, college, and competitive exams.'
    )
    db.session.add(academic)
    db.session.flush()  # Get the ID
    
    # School Subjects
    school_subjects = SubjectCategory(
        name='School Subjects',
        slug='school-subjects',
        description='K-12 curriculum support',
        parent_id=academic.id,
        icon_url='/static/icons/school.svg',
        color='#5CB85C',
        sort_order=1
    )
    db.session.add(school_subjects)
    db.session.flush()
    
    # Mathematics
    math_category = SubjectCategory(
        name='Mathematics',
        slug='mathematics',
        description='Mathematics from basics to advanced',
        parent_id=school_subjects.id,
        icon_url='/static/icons/math.svg',
        color='#F0AD4E',
        sort_order=1
    )
    db.session.add(math_category)
    db.session.flush()
    
    math_subjects = [
        {'name': 'Elementary Math', 'slug': 'elementary-math', 'description': 'Basic arithmetic and concepts for grades K-5', 'difficulty_level': 'Beginner', 'typical_duration_hours': 40, 'typical_price_range_min': 15, 'typical_price_range_max': 30},
        {'name': 'Middle School Math', 'slug': 'middle-school-math', 'description': 'Pre-algebra and geometry for grades 6-8', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 60, 'typical_price_range_min': 20, 'typical_price_range_max': 40},
        {'name': 'High School Math', 'slug': 'high-school-math', 'description': 'Algebra, geometry, trigonometry, and pre-calculus', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 80, 'typical_price_range_min': 25, 'typical_price_range_max': 50},
        {'name': 'Calculus', 'slug': 'calculus', 'description': 'Differential and integral calculus', 'difficulty_level': 'Advanced', 'typical_duration_hours': 100, 'typical_price_range_min': 40, 'typical_price_range_max': 80},
        {'name': 'Statistics', 'slug': 'statistics', 'description': 'Probability, statistics, and data analysis', 'difficulty_level': 'Advanced', 'typical_duration_hours': 80, 'typical_price_range_min': 35, 'typical_price_range_max': 70}
    ]
    
    for subject_data in math_subjects:
        subject = Subject(category_id=math_category.id, **subject_data)
        db.session.add(subject)
    
    # Science
    science_category = SubjectCategory(
        name='Science',
        slug='science',
        description='Physical and life sciences',
        parent_id=school_subjects.id,
        icon_url='/static/icons/science.svg',
        color='#D9534F',
        sort_order=2
    )
    db.session.add(science_category)
    db.session.flush()
    
    science_subjects = [
        {'name': 'Physics', 'slug': 'physics', 'description': 'Mechanics, electromagnetism, and modern physics', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 80, 'typical_price_range_min': 30, 'typical_price_range_max': 60},
        {'name': 'Chemistry', 'slug': 'chemistry', 'description': 'General, organic, and inorganic chemistry', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 80, 'typical_price_range_min': 30, 'typical_price_range_max': 60},
        {'name': 'Biology', 'slug': 'biology', 'description': 'Cell biology, genetics, and ecology', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 60, 'typical_price_range_min': 25, 'typical_price_range_max': 50},
        {'name': 'Environmental Science', 'slug': 'environmental-science', 'description': 'Ecology, climate science, and sustainability', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 60, 'typical_price_range_min': 25, 'typical_price_range_max': 50}
    ]
    
    for subject_data in science_subjects:
        subject = Subject(category_id=science_category.id, **subject_data)
        db.session.add(subject)
    
    # Competitive Exams
    competitive_exams = SubjectCategory(
        name='Competitive Exams',
        slug='competitive-exams',
        description='Test preparation for college entrance and professional exams',
        parent_id=academic.id,
        icon_url='/static/icons/exam.svg',
        color='#9B59B6',
        sort_order=2
    )
    db.session.add(competitive_exams)
    db.session.flush()
    
    exam_subjects = [
        {'name': 'JEE Preparation', 'slug': 'jee-preparation', 'description': 'Joint Entrance Examination for engineering', 'difficulty_level': 'Advanced', 'typical_duration_hours': 200, 'typical_price_range_min': 40, 'typical_price_range_max': 100},
        {'name': 'NEET Preparation', 'slug': 'neet-preparation', 'description': 'National Eligibility Entrance Test for medical', 'difficulty_level': 'Advanced', 'typical_duration_hours': 200, 'typical_price_range_min': 40, 'typical_price_range_max': 100},
        {'name': 'IELTS Preparation', 'slug': 'ielts-preparation', 'description': 'International English Language Testing System', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 60, 'typical_price_range_min': 25, 'typical_price_range_max': 60},
        {'name': 'TOEFL Preparation', 'slug': 'toefl-preparation', 'description': 'Test of English as a Foreign Language', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 60, 'typical_price_range_min': 25, 'typical_price_range_max': 60},
        {'name': 'GRE Preparation', 'slug': 'gre-preparation', 'description': 'Graduate Record Examinations', 'difficulty_level': 'Advanced', 'typical_duration_hours': 80, 'typical_price_range_min': 35, 'typical_price_range_max': 80},
        {'name': 'GMAT Preparation', 'slug': 'gmat-preparation', 'description': 'Graduate Management Admission Test', 'difficulty_level': 'Advanced', 'typical_duration_hours': 80, 'typical_price_range_min': 35, 'typical_price_range_max': 80}
    ]
    
    for subject_data in exam_subjects:
        subject = Subject(category_id=competitive_exams.id, **subject_data)
        db.session.add(subject)
    
    db.session.commit()
    print("✓ Academic categories and subjects created")

def seed_language_categories():
    """Create language learning categories"""
    
    languages = SubjectCategory(
        name='Languages & Communication',
        slug='languages-communication',
        description='Learn new languages and improve communication skills',
        icon_url='/static/icons/languages.svg',
        banner_url='/static/banners/languages.jpg',
        color='#E67E22',
        sort_order=2,
        is_featured=True,
        meta_title='Language Learning - Expert Tutors for 50+ Languages',
        meta_description='Learn languages with native speakers and certified tutors. English, Spanish, French, German, Chinese, Japanese and more.'
    )
    db.session.add(languages)
    db.session.flush()
    
    # Foreign Languages
    foreign_languages = SubjectCategory(
        name='Foreign Languages',
        slug='foreign-languages',
        description='International language learning',
        parent_id=languages.id,
        icon_url='/static/icons/foreign-languages.svg',
        color='#3498DB',
        sort_order=1
    )
    db.session.add(foreign_languages)
    db.session.flush()
    
    language_subjects = [
        {'name': 'English', 'slug': 'english', 'description': 'English language learning and proficiency', 'difficulty_level': 'All Levels', 'typical_duration_hours': 100, 'typical_price_range_min': 20, 'typical_price_range_max': 60},
        {'name': 'Spanish', 'slug': 'spanish', 'description': 'Spanish language from beginner to advanced', 'difficulty_level': 'All Levels', 'typical_duration_hours': 120, 'typical_price_range_min': 25, 'typical_price_range_max': 65},
        {'name': 'French', 'slug': 'french', 'description': 'French language and culture', 'difficulty_level': 'All Levels', 'typical_duration_hours': 120, 'typical_price_range_min': 25, 'typical_price_range_max': 65},
        {'name': 'German', 'slug': 'german', 'description': 'German language for business and travel', 'difficulty_level': 'All Levels', 'typical_duration_hours': 120, 'typical_price_range_min': 25, 'typical_price_range_max': 65},
        {'name': 'Chinese (Mandarin)', 'slug': 'chinese-mandarin', 'description': 'Mandarin Chinese language and culture', 'difficulty_level': 'All Levels', 'typical_duration_hours': 150, 'typical_price_range_min': 30, 'typical_price_range_max': 80},
        {'name': 'Japanese', 'slug': 'japanese', 'description': 'Japanese language and culture', 'difficulty_level': 'All Levels', 'typical_duration_hours': 150, 'typical_price_range_min': 30, 'typical_price_range_max': 80},
        {'name': 'Arabic', 'slug': 'arabic', 'description': 'Modern Standard Arabic and dialects', 'difficulty_level': 'All Levels', 'typical_duration_hours': 140, 'typical_price_range_min': 25, 'typical_price_range_max': 70}
    ]
    
    for subject_data in language_subjects:
        subject = Subject(category_id=foreign_languages.id, **subject_data)
        db.session.add(subject)
    
    # Regional Languages (India)
    regional_languages = SubjectCategory(
        name='Regional Languages (India)',
        slug='regional-languages-india',
        description='Indian regional languages',
        parent_id=languages.id,
        icon_url='/static/icons/regional-languages.svg',
        color='#E74C3C',
        sort_order=2
    )
    db.session.add(regional_languages)
    db.session.flush()
    
    regional_subjects = [
        {'name': 'Hindi', 'slug': 'hindi', 'description': 'Hindi language learning', 'difficulty_level': 'All Levels', 'typical_duration_hours': 80, 'typical_price_range_min': 15, 'typical_price_range_max': 40},
        {'name': 'Tamil', 'slug': 'tamil', 'description': 'Tamil language and literature', 'difficulty_level': 'All Levels', 'typical_duration_hours': 100, 'typical_price_range_min': 20, 'typical_price_range_max': 45},
        {'name': 'Telugu', 'slug': 'telugu', 'description': 'Telugu language learning', 'difficulty_level': 'All Levels', 'typical_duration_hours': 100, 'typical_price_range_min': 20, 'typical_price_range_max': 45},
        {'name': 'Bengali', 'slug': 'bengali', 'description': 'Bengali language and culture', 'difficulty_level': 'All Levels', 'typical_duration_hours': 100, 'typical_price_range_min': 20, 'typical_price_range_max': 45},
        {'name': 'Marathi', 'slug': 'marathi', 'description': 'Marathi language learning', 'difficulty_level': 'All Levels', 'typical_duration_hours': 80, 'typical_price_range_min': 15, 'typical_price_range_max': 40}
    ]
    
    for subject_data in regional_subjects:
        subject = Subject(category_id=regional_languages.id, **subject_data)
        db.session.add(subject)
    
    db.session.commit()
    print("✓ Language categories and subjects created")

def seed_hobbies_categories():
    """Create hobbies and lifestyle categories"""
    
    hobbies = SubjectCategory(
        name='Hobbies & Lifestyle',
        slug='hobbies-lifestyle',
        description='Develop new skills and pursue your passions',
        icon_url='/static/icons/hobbies.svg',
        banner_url='/static/banners/hobbies.jpg',
        color='#16A085',
        sort_order=3,
        is_featured=True,
        meta_title='Hobbies & Lifestyle Skills - Learn Music, Dance, Cooking, Art & More',
        meta_description='Discover your passion with expert tutors in music, dance, cooking, art, yoga, fitness, photography and more.'
    )
    db.session.add(hobbies)
    db.session.flush()
    
    # Music
    music = SubjectCategory(
        name='Music',
        slug='music',
        description='Learn musical instruments and theory',
        parent_id=hobbies.id,
        icon_url='/static/icons/music.svg',
        color='#8E44AD',
        sort_order=1
    )
    db.session.add(music)
    db.session.flush()
    
    music_subjects = [
        {'name': 'Guitar', 'slug': 'guitar', 'description': 'Acoustic and electric guitar lessons', 'difficulty_level': 'All Levels', 'typical_duration_hours': 60, 'typical_price_range_min': 25, 'typical_price_range_max': 60},
        {'name': 'Piano', 'slug': 'piano', 'description': 'Classical and contemporary piano', 'difficulty_level': 'All Levels', 'typical_duration_hours': 80, 'typical_price_range_min': 30, 'typical_price_range_max': 70},
        {'name': 'Violin', 'slug': 'violin', 'description': 'Classical violin techniques', 'difficulty_level': 'All Levels', 'typical_duration_hours': 100, 'typical_price_range_min': 35, 'typical_price_range_max': 80},
        {'name': 'Drums', 'slug': 'drums', 'description': 'Drum kit and percussion', 'difficulty_level': 'All Levels', 'typical_duration_hours': 60, 'typical_price_range_min': 30, 'typical_price_range_max': 65},
        {'name': 'Singing', 'slug': 'singing', 'description': 'Vocal training and singing techniques', 'difficulty_level': 'All Levels', 'typical_duration_hours': 50, 'typical_price_range_min': 25, 'typical_price_range_max': 55},
        {'name': 'Music Theory', 'slug': 'music-theory', 'description': 'Understanding music composition and theory', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 40, 'typical_price_range_min': 20, 'typical_price_range_max': 45}
    ]
    
    for subject_data in music_subjects:
        subject = Subject(category_id=music.id, **subject_data)
        db.session.add(subject)
    
    # Dance
    dance = SubjectCategory(
        name='Dance',
        slug='dance',
        description='Learn various dance forms',
        parent_id=hobbies.id,
        icon_url='/static/icons/dance.svg',
        color='#E74C3C',
        sort_order=2
    )
    db.session.add(dance)
    db.session.flush()
    
    dance_subjects = [
        {'name': 'Classical Dance', 'slug': 'classical-dance', 'description': 'Ballet, contemporary, and traditional forms', 'difficulty_level': 'All Levels', 'typical_duration_hours': 60, 'typical_price_range_min': 25, 'typical_price_range_max': 55},
        {'name': 'Hip-hop', 'slug': 'hip-hop', 'description': 'Street dance and hip-hop techniques', 'difficulty_level': 'All Levels', 'typical_duration_hours': 40, 'typical_price_range_min': 20, 'typical_price_range_max': 45},
        {'name': 'Salsa', 'slug': 'salsa', 'description': 'Latin dance and salsa techniques', 'difficulty_level': 'All Levels', 'typical_duration_hours': 50, 'typical_price_range_min': 25, 'typical_price_range_max': 50},
        {'name': 'Bollywood Dance', 'slug': 'bollywood-dance', 'description': 'Indian film dance styles', 'difficulty_level': 'All Levels', 'typical_duration_hours': 40, 'typical_price_range_min': 20, 'typical_price_range_max': 45}
    ]
    
    for subject_data in dance_subjects:
        subject = Subject(category_id=dance.id, **subject_data)
        db.session.add(subject)
    
    # Cooking
    cooking = SubjectCategory(
        name='Cooking',
        slug='cooking',
        description='Culinary skills and recipes',
        parent_id=hobbies.id,
        icon_url='/static/icons/cooking.svg',
        color='#D35400',
        sort_order=3
    )
    db.session.add(cooking)
    db.session.flush()
    
    cooking_subjects = [
        {'name': 'Indian Cooking', 'slug': 'indian-cooking', 'description': 'Traditional and modern Indian cuisine', 'difficulty_level': 'All Levels', 'typical_duration_hours': 40, 'typical_price_range_min': 20, 'typical_price_range_max': 50},
        {'name': 'Italian Cooking', 'slug': 'italian-cooking', 'description': 'Pasta, pizza, and Italian cuisine', 'difficulty_level': 'All Levels', 'typical_duration_hours': 35, 'typical_price_range_min': 25, 'typical_price_range_max': 55},
        {'name': 'Chinese Cooking', 'slug': 'chinese-cooking', 'description': 'Authentic Chinese dishes and techniques', 'difficulty_level': 'All Levels', 'typical_duration_hours': 35, 'typical_price_range_min': 25, 'typical_price_range_max': 55},
        {'name': 'Baking', 'slug': 'baking', 'description': 'Cakes, breads, and pastries', 'difficulty_level': 'All Levels', 'typical_duration_hours': 45, 'typical_price_range_min': 25, 'typical_price_range_max': 60}
    ]
    
    for subject_data in cooking_subjects:
        subject = Subject(category_id=cooking.id, **subject_data)
        db.session.add(subject)
    
    db.session.commit()
    print("✓ Hobby categories and subjects created")

def seed_it_categories():
    """Create IT and professional skills categories"""
    
    it_skills = SubjectCategory(
        name='IT & Professional Skills',
        slug='it-professional-skills',
        description='Technology skills and professional development',
        icon_url='/static/icons/it-skills.svg',
        banner_url='/static/banners/it-skills.jpg',
        color='#2C3E50',
        sort_order=4,
        is_featured=True,
        meta_title='IT & Professional Skills - Programming, Design, Business & More',
        meta_description='Master technology and business skills with expert tutors. Programming, web development, data science, digital marketing, and professional development.'
    )
    db.session.add(it_skills)
    db.session.flush()
    
    # Programming
    programming = SubjectCategory(
        name='Programming',
        slug='programming',
        description='Software development and coding',
        parent_id=it_skills.id,
        icon_url='/static/icons/programming.svg',
        color='#34495E',
        sort_order=1
    )
    db.session.add(programming)
    db.session.flush()
    
    programming_subjects = [
        {'name': 'Python', 'slug': 'python', 'description': 'Python programming for beginners to advanced', 'difficulty_level': 'All Levels', 'typical_duration_hours': 80, 'typical_price_range_min': 30, 'typical_price_range_max': 80},
        {'name': 'JavaScript', 'slug': 'javascript', 'description': 'JavaScript and modern web development', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 100, 'typical_price_range_min': 35, 'typical_price_range_max': 90},
        {'name': 'Java', 'slug': 'java', 'description': 'Java programming and enterprise development', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 120, 'typical_price_range_min': 40, 'typical_price_range_max': 100},
        {'name': 'C++', 'slug': 'cpp', 'description': 'C++ programming and system development', 'difficulty_level': 'Advanced', 'typical_duration_hours': 120, 'typical_price_range_min': 40, 'typical_price_range_max': 100},
        {'name': 'Web Development', 'slug': 'web-development', 'description': 'HTML, CSS, and full-stack development', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 100, 'typical_price_range_min': 35, 'typical_price_range_max': 85},
        {'name': 'Mobile App Development', 'slug': 'mobile-app-development', 'description': 'iOS and Android app development', 'difficulty_level': 'Advanced', 'typical_duration_hours': 120, 'typical_price_range_min': 45, 'typical_price_range_max': 120}
    ]
    
    for subject_data in programming_subjects:
        subject = Subject(category_id=programming.id, **subject_data)
        db.session.add(subject)
    
    # Data Science
    data_science = SubjectCategory(
        name='Data Science & AI',
        slug='data-science-ai',
        description='Data analysis, machine learning, and AI',
        parent_id=it_skills.id,
        icon_url='/static/icons/data-science.svg',
        color='#2980B9',
        sort_order=2
    )
    db.session.add(data_science)
    db.session.flush()
    
    data_subjects = [
        {'name': 'Data Analysis', 'slug': 'data-analysis', 'description': 'Data analysis with Excel, SQL, and Python', 'difficulty_level': 'Intermediate', 'typical_duration_hours': 80, 'typical_price_range_min': 35, 'typical_price_range_max': 85},
        {'name': 'Machine Learning', 'slug': 'machine-learning', 'description': 'ML algorithms and practical applications', 'difficulty_level': 'Advanced', 'typical_duration_hours': 120, 'typical_price_range_min': 50, 'typical_price_range_max': 120},
        {'name': 'Artificial Intelligence', 'slug': 'artificial-intelligence', 'description': 'AI concepts and implementation', 'difficulty_level': 'Advanced', 'typical_duration_hours': 140, 'typical_price_range_min': 55, 'typical_price_range_max': 150},
        {'name': 'Big Data', 'slug': 'big-data', 'description': 'Big data technologies and analytics', 'difficulty_level': 'Advanced', 'typical_duration_hours': 100, 'typical_price_range_min': 45, 'typical_price_range_max': 110}
    ]
    
    for subject_data in data_subjects:
        subject = Subject(category_id=data_science.id, **subject_data)
        db.session.add(subject)
    
    db.session.commit()
    print("✓ IT and professional skills categories created")

def seed_learning_objectives():
    """Add sample learning objectives for popular subjects"""
    
    # Get some popular subjects
    python = Subject.query.filter_by(slug='python').first()
    guitar = Subject.query.filter_by(slug='guitar').first()
    english = Subject.query.filter_by(slug='english').first()
    
    objectives_data = {
        python: [
            {'title': 'Master Python Syntax and Basics', 'description': 'Learn variables, data types, and control structures', 'sort_order': 1},
            {'title': 'Understand Object-Oriented Programming', 'description': 'Classes, objects, inheritance, and polymorphism', 'sort_order': 2},
            {'title': 'Work with Python Libraries', 'description': 'NumPy, Pandas, and other essential libraries', 'sort_order': 3},
            {'title': 'Build Real Projects', 'description': 'Apply knowledge to create practical applications', 'sort_order': 4}
        ],
        guitar: [
            {'title': 'Learn Basic Chords and Strumming', 'description': 'Master fundamental chords and rhythm patterns', 'sort_order': 1},
            {'title': 'Read Guitar Tablature', 'description': 'Understand and read guitar tabs', 'sort_order': 2},
            {'title': 'Play Popular Songs', 'description': 'Learn to play your favorite songs', 'sort_order': 3},
            {'title': 'Music Theory Basics', 'description': 'Understand scales, keys, and chord progressions', 'sort_order': 4}
        ],
        english: [
            {'title': 'Improve Speaking Fluency', 'description': 'Develop confident and natural speaking skills', 'sort_order': 1},
            {'title': 'Enhance Vocabulary', 'description': 'Expand your vocabulary with commonly used words', 'sort_order': 2},
            {'title': 'Master Grammar Rules', 'description': 'Understand and apply correct grammar', 'sort_order': 3},
            {'title': 'Practice Conversation Skills', 'description': 'Engage in real-world conversations', 'sort_order': 4}
        ]
    }
    
    for subject, objectives in objectives_data.items():
        if subject:
            for obj_data in objectives:
                objective = LearningObjective(subject_id=subject.id, **obj_data)
                db.session.add(objective)
    
    db.session.commit()
    print("✓ Learning objectives created")

def main():
    """Main function to seed all marketplace data"""
    app = create_app()
    
    with app.app_context():
        print("🌱 Seeding marketplace data...")
        
        # Clear existing data (optional - comment out if you want to preserve data)
        # SubjectLevel.query.delete()
        # LearningObjective.query.delete()
        # Subject.query.delete()
        # SubjectCategory.query.delete()
        # db.session.commit()
        
        # Seed data in order
        seed_subject_levels()
        seed_academic_categories()
        seed_language_categories()
        seed_hobbies_categories()
        seed_it_categories()
        seed_learning_objectives()
        
        print("✅ Marketplace data seeding completed successfully!")
        print(f"📊 Created {SubjectCategory.query.count()} categories")
        print(f"📚 Created {Subject.query.count()} subjects")
        print(f"🎯 Created {LearningObjective.query.count()} learning objectives")
        print(f"📈 Created {SubjectLevel.query.count()} proficiency levels")

if __name__ == '__main__':
    main()