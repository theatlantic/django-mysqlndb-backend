try:
    import MySQLdb as Database
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading MySQLdb module: %s" % e)

from weakref import proxy
import types

import random

from django.db.backends import BaseDatabaseWrapper
from django.db.backends.mysql import base as mysqlbase

from django.db.backends.mysql.client import DatabaseClient
from django.db.backends.mysql.introspection import DatabaseIntrospection
from django.db.backends.mysql.validation import DatabaseValidation

# Our one overridden class
from .creation import DatabaseCreation

# Don't raise exceptions for database warnings if DEBUG is on
# (this overrides django behavior)
from django.conf import settings
if settings.DEBUG:
    from warnings import filterwarnings
    filterwarnings("always", category=Database.Warning)

from django.utils.safestring import SafeUnicode, SafeString

class DatabaseFeatures(mysqlbase.DatabaseFeatures):
    supports_foreign_keys = True
    _storage_engine = None

    def get_storage_engine(self):
        if self._storage_engine is None:
            cursor = self.connection.cursor()
            db_name = 'INTROSPECTION_TEST_%d' % random.randint(1, 1000000)
            cursor.execute('CREATE TABLE %s (X INT)' % db_name)
            # This command is MySQL specific; the second column
            # will tell you the default table type of the created
            # table. Since all Django's test tables will have the same
            # table type, that's enough to evaluate the feature.
            cursor.execute('SHOW TABLE STATUS WHERE Name="%s"' % db_name)
            result = cursor.fetchone()
            cursor.execute('DROP TABLE %s' % db_name)
            self._storage_engine = result[1]
        return self._storage_engine

    storage_engine = property(get_storage_engine)

    def confirm(self):
        """
        Perform manual checks of any database features that might vary between installs
        """
        self._confirmed = True
        self.supports_transactions = self._supports_transactions()
        self.supports_stddev = self._supports_stddev()
        self.can_introspect_foreign_keys = self.storage_engine not in ('MyISAM', 'ndbcluster',)
        self.supports_foreign_keys = self.storage_engine != 'ndbcluster'

class DatabaseOperations(mysqlbase.DatabaseOperations):
    pass

class DatabaseWrapper(mysqlbase.DatabaseWrapper):
    def __init__(self, *args, **kwargs):
        BaseDatabaseWrapper.__init__(self, *args, **kwargs)

        self.server_version = None
        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations()
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = DatabaseValidation(self)

    def _cursor(self):
        """
        django.db.backends.mysql.base.DatabaseWrapper._cursor() instantiates
        the MySQLdb object. This override modifies the string decoder to support
        storing and retrieving unicode strings in a database where the charset
        is latin1.
        
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