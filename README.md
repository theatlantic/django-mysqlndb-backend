django-mysqlndb-backend
=======================

**django-mysqlndb-backend** is a project that provides a django database
backend that works with **MySQL Cluster**. The MySQL backend provided by
django does not currently work with **MySQL Cluster** because of [a bug
in the handling of foreign key
constructs](http://bugs.mysql.com/bug.php?id=58929). The backend provided in
this module extends and overrides the behavior of django's MySQL database
backend to suppress foreign key constraints in `ALTER TABLE` and `CREATE TABLE`
constructs.

Installation
------------

The recommended way to install from source is with pip:

    $ pip install -e git+git://github.com/theatlantic/django-mysqlndb-backend.git#egg=django-mysqlndb-backend

If the source is already checked out, use setuptools:

    $ python setup.py install

Usage
-----

When defining your database in settings.py, set `ENGINE` to `'mysqlndb'`
rather than `'django.db.backends.mysql'` / `'mysql'`.

```python
DATABASES = {
    'default': {
        'OPTIONS': {
            'init_command': 'SET storage_engine=ndbcluster',
        },
        'ENGINE': 'mysqlndb',
        'NAME': 'database_name',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```
