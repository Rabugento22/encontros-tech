from unittest.mock import MagicMock
from sqlalchemy.exc import OperationalError

from services import health_service


def test_check_liveness_returns_ok():
    # Act
    result = health_service.check_liveness()

    # Assert
    assert result == {"status": "ok"}


def test_check_readiness_when_database_is_up():
    # Arrange
    mock_db = MagicMock()

    # Act
    is_ready, reason = health_service.check_readiness(mock_db)

    # Assert
    assert is_ready is True
    assert reason is None
    mock_db.execute.assert_called_once()


def test_check_readiness_when_database_is_down():
    # Arrange
    mock_db = MagicMock()
    mock_db.execute.side_effect = OperationalError(
        "SELECT 1", {}, Exception("connection refused\nDetalhe interno")
    )

    # Act
    is_ready, reason = health_service.check_readiness(mock_db)

    # Assert
    assert is_ready is False
    assert "connection refused" in reason
    assert "\n" not in reason  # apenas a primeira linha do erro
