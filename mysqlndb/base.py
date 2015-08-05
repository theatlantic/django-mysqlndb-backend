try:
    import MySQLdb as Database
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading MySQLdb module: %s" % e)

import inspect
from weakref import proxy
import types

import random

from django.db.backends.mysql import base as mysqlbase

BaseDatabaseWrapper = None
try:
    # Django 1.8
    from django.db.backends.base.base import BaseDatabaseWrapper
except ImportError:
    pass

if not BaseDatabaseWrapper or not issubclass(mysqlbase.DatabaseWrapper, BaseDatabaseWrapper):
    from django.db.backends import BaseDatabaseWrapper


from django.db.backends.mysql.client import DatabaseClient
from django.db.backends.mysql.introspection import DatabaseIntrospection
from django.db.backends.mysql.validation import DatabaseValidation
from django.db.utils import DatabaseError

from django.utils.safestring import SafeUnicode

# Our one overridden class
from .creation import DatabaseCreation


# Don't raise exceptions for database warnings
from warnings import filterwarnings
filterwarnings("always", category=Database.Warning)


class DatabaseFeatures(mysqlbase.DatabaseFeatures):
    supports_foreign_keys = True
    _storage_engine = None

    @property
    def storage_engine(self):
        if self._storage_engine is None:
            self._storage_engine = 'UNKNOWN'
            try:
                cursor = self.connection.cursor()
                cursor.execute('SHOW ENGINES')
                rows = cursor.fetchall()
                if rows:
                    try:
                        self._storage_engine = [r[0] for r in rows if r[1] == 'DEFAULT'][0]
                    except IndexError:
                        pass
            except (Database.OperationalError, DatabaseError):
                pass
        return self._storage_engine

    def confirm(self):
        """
        Perform manual checks of any database features that might vary between
        installs
        """
        self._confirmed = True
        self.supports_transactions = self.storage_engine in ('InnoDB', 'ndbcluster', 'BDB')
        # Django 1.5 forward compatibility check
        if not hasattr(self, 'supports_stddev'):
            self.supports_stddev = self._supports_stddev()
        self.can_introspect_foreign_keys = self.storage_engine not in ('MyISAM', 'ndbcluster',)
        self.supports_foreign_keys = self.storage_engine != 'ndbcluster'


class DatabaseOperations(mysqlbase.DatabaseOperations):

    def __init__(self, connection):
        """
        Compatibility wrapper for Django 1.4 and Django <= 1.3.

        In Django 1.4, DatabaseOperations.__init__() takes connection as an
        argument, whereas in Django <= 1.3 there are no extra arguments to
        DatabaseOperations.__init__().
        """
        super_init = super(DatabaseOperations, self).__init__
        ops_args = inspect.getargspec(super_init)[0]
        if len(ops_args) == 2:
            # Django 1.4
            super_init(connection)
        else:
            # Django <= 1.3
            super_init()


class DatabaseWrapper(mysqlbase.DatabaseWrapper):

    def __init__(self, *args, **kwargs):
        BaseDatabaseWrapper.__init__(self, *args, **kwargs)

        self.server_version = None
        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = DatabaseValidation(self)

    def _cursor(self):
        """
        django.db.backends.mysql.base.DatabaseWrapper._cursor() instantiates
        the MySQLdb object. This override modifies the string decoder to
        support storing and retrieving unicode strings in a database where the
        charset is latin1.

        If the charset is latin1:
          - `unicode` objects are decoded to a byte string before saving.
          - `str` objects returned from the database are encoded with the
            'utf8' codec, not 'latin1'.
        """
        cursor = super(DatabaseWrapper, self)._cursor()
        connection = self.connection
        charset = connection.character_set_name()
        charset_fix_applied = hasattr(connection.string_decoder, 'charset_fix_applied')
        if charset != 'utf' and not charset_fix_applied:
            def _get_string_decoder():
                def string_decoder(s):
                    string_decoder_charset = string_decoder.charset
                    if string_decoder.charset == 'latin1':
                        string_decoder_charset = 'utf8'
                    return s.decode(string_decoder_charset)
                return string_decoder

            connection.string_decoder = string_decoder = _get_string_decoder()
            connection.string_decoder.charset = charset
            connection.string_decoder.charset_fix_applied = True
            connection.converter[Database.FIELD_TYPE.STRING][-1:] = [(None, string_decoder)]
            connection.converter[Database.FIELD_TYPE.VAR_STRING][-1:] = [(None, string_decoder)]
            connection.converter[Database.FIELD_TYPE.VARCHAR][-1:] = [(None, string_decoder)]
            connection.converter[Database.FIELD_TYPE.BLOB][-1:] = [(None, string_decoder)]

            db = proxy(connection)
            def _get_unicode_literal():
                def unicode_literal(u, dummy=None):
                    unicode_literal_charset = unicode_literal.charset
                    if string_decoder.charset == 'latin1':
                        unicode_literal_charset = 'utf8'
                    return db.literal(u.encode(unicode_literal_charset))
                return unicode_literal

            connection.unicode_literal = unicode_literal = _get_unicode_literal()
            connection.unicode_literal.charset = charset
            connection.encoders[types.UnicodeType] = unicode_literal
            connection.encoders[SafeUnicode] = unicode_literal

        return cursor
