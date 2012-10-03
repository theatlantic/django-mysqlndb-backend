from distutils.core import setup

setup(
    name='django-mysqlndb-backend',
    version='1.0.2',
    author_email='ATMOprogrammers@theatlantic.com',
    packages=['mysqlndb'],
    url='https://github.com/theatlantic/django-mysqlndb-backend',
    description='Provides a django database backend that works with MySQL Cluster\'s NDB storage engine.',
    install_requires=[
    	"Django >= 1.2",
        "MySQL-python >= 1.2.2",
    ],
)
