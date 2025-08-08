SEARCH_CONFIG = {
    'days_back': 30,
    'categories': ['cs.LG', 'q-bio'],
    'operator': 'AND',
    'include_cross_list': True,
    'results_per_page': 100
}

DATA_CONFIG = {
    'data_dir': 'data',
    'papers_file': 'papers.json'
}

LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'logs/app.log'
}