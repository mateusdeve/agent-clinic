import os
from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv

# Carrega variaveis de ambiente do arquivo .env
load_dotenv()

# Objeto de configuracao do Alembic — acesso ao .ini
config = context.config

# Configura logging conforme arquivo .ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Sem modelos SQLAlchemy — todas as migrations usam SQL puro via op.execute()
target_metadata = None


def run_migrations_offline() -> None:
    """Executa migrations em modo 'offline'.

    Configura o contexto apenas com a URL, sem criar Engine.
    """
    url = os.getenv("DATABASE_URL")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrations em modo 'online'.

    Le DATABASE_URL do ambiente e cria Engine com NullPool
    (sem pooling — adequado para execucao de migrations).
    """
    url = os.getenv("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
