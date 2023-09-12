from fastapi_mail import ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME = "repogranular@gmail.com",
    MAIL_PASSWORD = "zswtnpjbgrkekdoa",
    MAIL_FROM = "repogranular@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
)