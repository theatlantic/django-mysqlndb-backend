import copy

import MySQLdb as Database
from django.db.backends.mysql import creation


class DatabaseCreation(creation.DatabaseCreation):
    supports_foreign_keys = True

    def __init__(self, connection):
        super(DatabaseCreation, self).__init__(connection)
        self.connection.features.confirm()
        self.supports_foreign_keys = getattr(self.connection.features, "supports_foreign_keys", True)

    def sql_for_inline_foreign_key_references(self, field, known_models, style):
        if not self.supports_foreign_keys or not getattr(field, 'db_constraint', True):
            return [], False
        return super(DatabaseCreation, self).sql_for_inline_foreign_key_references(field, known_models, style)

    def sql_remove_table_constraints(self, model, references_to_delete, style):
        if not self.supports_foreign_keys:
            return []
        return super(DatabaseCreation, self).sql_remove_table_constraints(model, references_to_delete, style)

    def sql_for_pending_references(self, model, style, pending_references):
        if not self.supports_foreign_keys:
            return []
        elif model in pending_references:
            references = copy.deepcopy(pending_references)
            pending_references = []
            for rel_class, f in references:
                if getattr(f, 'db_constraint', True):
                    pending_references.append((rel_class, f))
        return super(DatabaseCreation, self).sql_for_pending_references(model, style, pending_references)
