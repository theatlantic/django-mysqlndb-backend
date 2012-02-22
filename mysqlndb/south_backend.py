from south.db.mysql import DatabaseOperations as BaseDatabaseOperations

class DatabaseOperations(BaseDatabaseOperations):
    def connection_init(self):
        super(DatabaseOperations, self).connection_init()
        connection = self._get_connection()
        self.supports_foreign_keys = getattr(connection.features, "supports_foreign_keys", True)
