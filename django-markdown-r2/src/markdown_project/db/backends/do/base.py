from django_cf.db.backends.do.base import DatabaseWrapper as DjangoCFDatabaseWrapper
from django_cf.db.backends.do.storage import get_storage
from django_cf.db.base_engine import CFResult


class DatabaseWrapper(DjangoCFDatabaseWrapper):
    def run_query(self, query, params=None) -> CFResult:
        processed_query, params = self.process_query(query, params)
        db = get_storage()
        statement = (
            db.exec(processed_query, *params) if params else db.exec(processed_query)
        )

        rows = statement.raw().toArray()
        if not isinstance(rows, list):
            rows = rows.to_py()

        return CFResult.from_object(
            query,
            params,
            rows,
            statement.rowsRead,
            statement.rowsWritten,
        )
