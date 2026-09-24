import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '_moldx.settings')
import django
django.setup()

from django.urls import get_resolver
resolver = get_resolver()

def walk(p, prefix=''):
    for url in p.url_patterns:
        path = prefix + str(url.pattern)
        if hasattr(url, 'url_patterns'):
            walk(url, path)
        elif 'dashboard' in path.lower() or 'statistics' in path.lower():
            print('FOUND:', path)

walk(resolver)
print('URL scan done')