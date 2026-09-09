import mysql.connector

import app


def test_get_db_connection_falls_back_to_sqlite(monkeypatch):
    def raise_interface_error(**kwargs):
        raise mysql.connector.InterfaceError("Can't connect to MySQL server")

    monkeypatch.setattr(app, "DB_CONFIG", {"host": "localhost", "user": "root", "password": "", "database": "cow_qr_demo"})
    monkeypatch.setattr(app, "DB_TYPE", "mysql")
    monkeypatch.setattr(app.mysql.connector, "connect", raise_interface_error)

    conn = app.get_db_connection()

    try:
        row = conn.execute("SELECT 1 AS value").fetchone()
        assert row[0] == 1
    finally:
        conn.close()
