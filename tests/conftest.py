import asyncio
import threading

import pytest

pytest_plugins = ["pytest_homeassistant_custom_component"]

# Python 3.12 asyncio calls shutdown_default_executor() in teardown, which
# starts a _run_safe_shutdown_loop thread. The plugin's verify_cleanup fixture
# does the same call and then flags that thread as unexpected. Override the
# fixture to allow it.
@pytest.fixture(autouse=True)
def verify_cleanup(event_loop, expected_lingering_tasks, expected_lingering_timers):
    threads_before = frozenset(threading.enumerate())
    tasks_before = asyncio.all_tasks(event_loop)
    yield

    event_loop.run_until_complete(event_loop.shutdown_default_executor())

    tasks = asyncio.all_tasks(event_loop) - tasks_before
    for task in tasks:
        if expected_lingering_tasks:
            pass
        else:
            pytest.fail(f"Lingering task after test {task!r}")
        task.cancel()
    if tasks:
        event_loop.run_until_complete(asyncio.wait(tasks))

    threads = frozenset(threading.enumerate()) - threads_before
    for thread in threads:
        if not (
            isinstance(thread, threading._DummyThread)
            or thread.name.startswith("waitpid-")
            or "_run_safe_shutdown_loop" in thread.name  # Python 3.12 executor shutdown thread
        ):
            pytest.fail(f"Lingering thread after test {thread!r}")
