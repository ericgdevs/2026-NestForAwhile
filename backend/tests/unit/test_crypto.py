from cryptography.fernet import Fernet
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, select

from app.crypto import EncryptedText, decrypt_value, encrypt_value


def test_encrypt_round_trip_does_not_store_plaintext():
    key = Fernet.generate_key().decode()
    metadata = MetaData()
    secrets = Table(
        "secrets",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("value", EncryptedText(key)),
    )
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(secrets.insert().values(value="synthetic dietary profile"))
        raw = connection.exec_driver_sql("select value from secrets").scalar_one()
        decrypted = connection.execute(select(secrets.c.value)).scalar_one()

    assert "synthetic dietary profile" not in raw
    assert decrypted == "synthetic dietary profile"
    assert decrypt_value(encrypt_value("hello", key), key) == "hello"
