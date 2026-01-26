"""Tests for autoskope_client API."""

import pytest
from aiohttp import ClientSession
from unittest.mock import AsyncMock, MagicMock, patch

from autoskope_client import AutoskopeApi, CannotConnect, InvalidAuth


class TestAutoskopeApiInit:
    """Test AutoskopeApi initialization."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )

        assert api._host == "https://portal.autoskope.de"
        assert api._username == "test_user"
        assert api._password == "test_pass"
        assert api._owns_session is True
        assert api._session is None
        assert api._authenticated is False

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from host."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de/",
            username="test_user",
            password="test_pass",
        )

        assert api._host == "https://portal.autoskope.de"

    def test_init_with_external_session(self):
        """Test initialization with external session."""
        mock_session = MagicMock(spec=ClientSession)
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
            session=mock_session,
        )

        assert api._session is mock_session
        assert api._owns_session is False
        assert api._cookie_jar is None

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
            timeout=30,
        )

        assert api._timeout == 30

    def test_init_invalid_url_raises_error(self):
        """Test that invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Host must be a valid HTTP\\(S\\) URL"):
            AutoskopeApi(
                host="portal.autoskope.de",  # Missing http(s)://
                username="test_user",
                password="test_pass",
            )

        with pytest.raises(ValueError, match="Host must be a valid HTTP\\(S\\) URL"):
            AutoskopeApi(
                host="ftp://portal.autoskope.de",  # Wrong protocol
                username="test_user",
                password="test_pass",
            )


class TestAutoskopeApiProperties:
    """Test AutoskopeApi properties."""

    def test_is_connected_false_no_session(self):
        """Test is_connected returns False when no session."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )

        assert api.is_connected is False

    def test_is_connected_false_not_authenticated(self):
        """Test is_connected returns False when not authenticated."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )
        api._session = MagicMock(spec=ClientSession)
        api._authenticated = False

        assert api.is_connected is False

    def test_is_connected_true(self):
        """Test is_connected returns True when session exists and authenticated."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )
        api._session = MagicMock(spec=ClientSession)
        api._authenticated = True

        assert api.is_connected is True


@pytest.mark.asyncio
class TestAutoskopeApiConnect:
    """Test AutoskopeApi connect method."""

    async def test_connect_creates_session_and_authenticates(self):
        """Test that connect creates session and authenticates."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )

        with patch.object(api, "authenticate", new_callable=AsyncMock) as mock_auth:
            await api.connect()

            assert api._session is not None
            assert api._owns_session is True
            mock_auth.assert_called_once()

    async def test_connect_with_external_session(self):
        """Test connect with external session doesn't create new one."""
        mock_session = MagicMock(spec=ClientSession)
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
            session=mock_session,
        )

        with patch.object(api, "authenticate", new_callable=AsyncMock) as mock_auth:
            await api.connect()

            assert api._session is mock_session
            mock_auth.assert_called_once()

    async def test_connect_already_authenticated_skips_auth(self):
        """Test connect skips authentication if already authenticated."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )
        api._authenticated = True

        with patch.object(api, "authenticate", new_callable=AsyncMock) as mock_auth:
            await api.connect()

            mock_auth.assert_not_called()


@pytest.mark.asyncio
class TestAutoskopeApiClose:
    """Test AutoskopeApi close method."""

    async def test_close_owned_session(self):
        """Test close closes owned session."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )
        mock_session = AsyncMock(spec=ClientSession)
        api._session = mock_session
        api._owns_session = True
        api._authenticated = True

        await api.close()

        mock_session.close.assert_called_once()
        assert api._session is None
        assert api._authenticated is False

    async def test_close_external_session(self):
        """Test close doesn't close external session."""
        mock_session = AsyncMock(spec=ClientSession)
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
            session=mock_session,
        )
        api._authenticated = True

        await api.close()

        mock_session.close.assert_not_called()
        assert api._session is mock_session
        assert api._authenticated is False


@pytest.mark.asyncio
class TestAutoskopeApiContextManager:
    """Test AutoskopeApi as context manager."""

    async def test_context_manager_success(self):
        """Test context manager connects and closes properly."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )

        with patch.object(api, "connect", new_callable=AsyncMock) as mock_connect:
            with patch.object(api, "close", new_callable=AsyncMock) as mock_close:
                async with api as context_api:
                    assert context_api is api
                    mock_connect.assert_called_once()

                mock_close.assert_called_once()

    async def test_context_manager_cleanup_on_error(self):
        """Test context manager cleans up on connect error."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )

        with patch.object(
            api, "connect", new_callable=AsyncMock, side_effect=InvalidAuth("Test error")
        ):
            with patch.object(api, "close", new_callable=AsyncMock) as mock_close:
                with pytest.raises(InvalidAuth):
                    async with api:
                        pass

                mock_close.assert_called_once()


@pytest.mark.asyncio
class TestAutoskopeApiRequest:
    """Test AutoskopeApi _request method."""

    async def test_request_raises_if_not_connected(self):
        """Test _request raises RuntimeError if not connected."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )

        with pytest.raises(RuntimeError, match="Not connected"):
            await api._request("GET", "/test")


@pytest.mark.asyncio
class TestAutoskopeApiAuthenticate:
    """Test AutoskopeApi authenticate method."""

    async def test_authenticate_raises_if_no_session(self):
        """Test authenticate raises RuntimeError if no session."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )

        with pytest.raises(RuntimeError, match="Not connected"):
            await api.authenticate()


@pytest.mark.asyncio
class TestAutoskopeApiGetVehicles:
    """Test AutoskopeApi get_vehicles method."""

    async def test_get_vehicles_raises_if_not_connected(self):
        """Test get_vehicles raises RuntimeError if not connected."""
        api = AutoskopeApi(
            host="https://portal.autoskope.de",
            username="test_user",
            password="test_pass",
        )

        with pytest.raises(RuntimeError, match="Not connected"):
            await api.get_vehicles()
