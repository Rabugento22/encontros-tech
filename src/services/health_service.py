from typing import Optional, Tuple
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from core.logging import get_logger

logger = get_logger("health_service")

def check_liveness() -> dict:
    """Liveness: apenas indica que o processo está vivo, sem checar dependências"""
    return {"status": "ok"}

def check_readiness(db: Session) -> Tuple[bool, Optional[str]]:
    """Readiness: executa uma query simples no PostgreSQL.

    Retorna (True, None) se o banco responde, ou (False, motivo) se a conexão falhar.
    A exceção é contida aqui para não derrubar a aplicação.
    """
    try:
        db.execute(text("SELECT 1"))
        return True, None
    except SQLAlchemyError as e:
        # Apenas a primeira linha: o driver costuma anexar detalhes longos
        reason = (str(e.orig) if getattr(e, "orig", None) else str(e)).strip().splitlines()[0]
        logger.warning(f"Readiness falhou: {reason}")
        return False, reason
