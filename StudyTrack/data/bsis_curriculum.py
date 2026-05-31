BSIS_CURRICULUM = [
    {
        'year': '1',
        'semester': '1',
        'subjects': [
            'Understanding the Self',
            'Readings in Philippine History',
            'The Contemporary World',
            'Mathematics in the Modern World',
            'Purposive Communication',
            'Introduction to Computing',
            'Computer Programming 1',
            'Physical Education 1',
            'National Service Training Program 1',
        ],
    },
    {
        'year': '1',
        'semester': '2',
        'subjects': [
            'Art Appreciation',
            'Ethics',
            'Science, Technology and Society',
            'Discrete Mathematics',
            'Computer Programming 2',
            'Physical Education 2',
            'National Service Training Program 2',
        ],
    },
    {
        'year': '2',
        'semester': '1',
        'subjects': [
            'The Life and Works of Rizal',
            'Data Structures and Algorithms',
            'Object-Oriented Programming',
            'Database Management Systems',
            'Platform Technologies',
            'Networking 1',
            'Information Management',
            'Physical Education 3',
        ],
    },
    {
        'year': '2',
        'semester': '2',
        'subjects': [
            'Systems Analysis and Design',
            'Web Systems and Technologies',
            'Networking 2',
            'Information Assurance and Security',
            'Human-Computer Interaction',
            'Research Methods in Information Systems',
            'Physical Education 4',
        ],
    },
    {
        'year': '3',
        'semester': '1',
        'subjects': [
            'Advanced Database Systems',
            'Enterprise Architecture',
            'IT Project Management',
            'Applications Development and Emerging Technologies',
            'Business Analytics',
            'Information Systems Elective 1',
        ],
    },
    {
        'year': '3',
        'semester': '2',
        'subjects': [
            'Systems Integration and Architecture',
            'Business Process Management',
            'Data Warehousing and Analytics',
            'Research in Information Systems',
            'Information Systems Elective 2',
            'Professional Ethics and Governance',
        ],
    },
    {
        'year': '4',
        'semester': '1',
        'subjects': [
            'Capstone Project 1',
            'Practicum 1',
            'Information Systems Audit',
            'IT Security Management',
            'Information Systems Elective 3',
        ],
    },
    {
        'year': '4',
        'semester': '2',
        'subjects': [
            'Capstone Project 2',
            'Practicum 2',
            'Enterprise Resource Planning',
            'Information Systems Elective 4',
            'Seminar in Information Systems',
        ],
    },
]


def iter_curriculum_subjects():
    for term in BSIS_CURRICULUM:
        year = term['year']
        semester = term['semester']
        for subject_name in term['subjects']:
            yield {
                'name': subject_name,
                'year': year,
                'semester': semester,
            }

