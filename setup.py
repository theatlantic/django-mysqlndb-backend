import sys
import django

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup



install_requires = [
    'Django >= 1.8',
    'mysqlclient>=1.3.6' if sys.version_info[0] == 3 else 'MySQL-python>=1.2.5',
    'six>=1.10.0',
]

if django.VERSION < (1, 9):
    install_requires.append('django-transaction-hooks >= 0.2')


setup(
    name='django-mysqlndb-backend',
    version='1.2',
    author_email='programmers@theatlantic.com',
    packages=['mysqlndb'],
    url='https://github.com/theatlantic/django-mysqlndb-backend',
    description='Provides a django database backend that works with MySQL Cluster\'s NDB storage engine.',
    install_requires=install_requires,
)
