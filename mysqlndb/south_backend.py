import django

if django.VERSION < (1, 7):
    from south.db.mysql import DatabaseOperations as BaseDatabaseOperations
else:
    from django.db.backends.mysql.base import DatabaseOperations as BaseDatabaseOperations


class DatabaseOperations(BaseDatabaseOperations):

    def connection_init(self):
        super(DatabaseOperations, self).connection_init()
        connection = self._get_connection()
        self.supports_foreign_keys = getattr(connection.features, "supports_foreign_keys", True)

    def alter_column(self, table_name, name, field, *args, **kwargs):
        if not getattr(field, 'db_constraint', True):
            kwargs['ignore_constraints'] = True
        return super(DatabaseOperations, self).alter_column(table_name, name, field, *args, **kwargs)

    def column_sql(self, table_name, field_name, field, *args, **kwargs):
        supports_foreign_keys = self.supports_foreign_keys
        if not getattr(field, 'db_constraint', True):
            self.supports_foreign_keys = False
        retval = super(DatabaseOperations, self).column_sql(table_name, field_name, field, *args, **kwargs)
        self.supports_foreign_keys = supports_foreign_keys
        return retval
