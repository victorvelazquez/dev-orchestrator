"""Async utility functions."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import Any, Callable, TypeVar


T = TypeVar("T")

# Shared thread pool for sync operations
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="sync_worker")


async def run_sync(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Run a synchronous function in a thread pool.
    
    This allows blocking operations to run without blocking the event loop.
    
    Args:
        func: Synchronous function to run
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the function call
        
    Example:
        result = await run_sync(some_blocking_io, param1, param2)
    """
    loop = asyncio.get_event_loop()
    
    if kwargs:
        func = partial(func, **kwargs)
    
    return await loop.run_in_executor(_executor, func, *args)


def async_wrap(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to wrap a sync function for async execution.
    
    Example:
        @async_wrap
        def blocking_operation(x):
            time.sleep(1)
            return x * 2
        
        # Now can be used with await
        result = await blocking_operation(5)
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        return await run_sync(func, *args, **kwargs)
    
    return wrapper


async def gather_with_limit(
    tasks: list[Any],
    limit: int = 5,
) -> list[Any]:
    """
    Run async tasks with concurrency limit.
    
    Args:
        tasks: List of coroutines to run
        limit: Maximum concurrent tasks
        
    Returns:
        List of results in same order as input tasks
    """
    semaphore = asyncio.Semaphore(limit)
    
    async def limited_task(task: Any) -> Any:
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[limited_task(t) for t in tasks])


async def timeout_wrapper(
    coro: Any,
    timeout_seconds: float,
    default: T | None = None,
) -> T | None:
    """
    Run a coroutine with timeout.
    
    Args:
        coro: Coroutine to run
        timeout_seconds: Timeout in seconds
        default: Value to return on timeout
        
    Returns:
        Result of coroutine or default on timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        return default
