try:
    import MySQLdb as Database
except ImportError, e:
    from django.core.exceptions import ImproperlyConfigured

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

class DatabaseFeatures(mysqlbase.DatabaseFeatures):
    supports_foreign_keys = True
    _storage_engine = None

    def get_storage_engine(self):
        if self._storage_engine is None:
            cursor = self.connection.cursor()
            cursor.execute('CREATE TABLE INTROSPECT_TEST (X INT)')
            # This command is MySQL specific; the second column
            # will tell you the default table type of the created
            # table. Since all Django's test tables will have the same
            # table type, that's enough to evaluate the feature.
            cursor.execute('SHOW TABLE STATUS WHERE Name="INTROSPECT_TEST"')
            result = cursor.fetchone()
            cursor.execute('DROP TABLE INTROSPECT_TEST')
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
