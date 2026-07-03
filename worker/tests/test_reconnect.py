import pytest


class TestReconnect:
    def test_retry_handler_initial_state(self):
        from app.utils.retry import RetryHandler

        retry = RetryHandler()
        assert retry.attempt == 0
        assert retry.current_delay == 1

    @pytest.mark.asyncio
    async def test_retry_handler_increment(self):
        from app.utils.retry import RetryHandler

        retry = RetryHandler()
        await retry.wait()
        assert retry.attempt == 1

    def test_retry_handler_reset(self):
        from app.utils.retry import RetryHandler

        retry = RetryHandler()
        retry._attempt = 3
        retry.reset()
        assert retry.attempt == 0

    def test_retry_delays(self):
        from app.utils.retry import RetryHandler
        from app.core.constants import RETRY_DELAYS

        retry = RetryHandler([1, 2, 5])
        assert retry.current_delay == 1
        retry._attempt = 1
        assert retry.current_delay == 2
        retry._attempt = 2
        assert retry.current_delay == 5
        retry._attempt = 10
        assert retry.current_delay == 5
