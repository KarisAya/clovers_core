import inspect
from collections.abc import Coroutine, Callable

from .plugin import Plugin


class AdapterException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class AdapterMethod:
    kwarg = {}
    send = {}

    def get_kwarg(self, method_name: str) -> Callable:
        """添加一个获取参数方法"""

        def decorator(func: Coroutine):
            self.kwarg[method_name] = self.kwfilter(func)

        return decorator

    def send_message(self, method_name: str) -> Callable:
        """添加一个发送消息方法"""

        def decorator(func: Coroutine):
            self.send[method_name] = func

        return decorator

    @staticmethod
    def kwfilter(func: Coroutine):
        kw = inspect.signature(func).parameters.keys()

        async def wrapper(*args, **kwargs):
            return await func(*args, **{k: v for k, v in kwargs.items() if k in kw})

        return wrapper


class Adapter:
    def __init__(self) -> None:
        self.method: AdapterMethod = AdapterMethod()
        self.plugins: list[Plugin] = []

    async def response(self, command: str, **kwargs) -> int:
        flag = 0
        for plugin in self.plugins:
            resp = plugin(command)
            for key, event in resp.items():
                handle = plugin.handles[key]
                for kw in handle.extra_args:
                    get_kwarg = self.method.kwarg.get(kw)
                    if not get_kwarg:
                        raise AdapterException(f"使用了未定义的 get_kwarg 方法:{kw}")
                    event.kwargs[kw] = await get_kwarg(**kwargs)
                result = await handle(event)
                if result:
                    flag += 1
                    send_method = result.send_method
                    send = self.method.send.get(send_method)
                    if not send:
                        raise AdapterException(f"使用了未定义的 send 方法:{send_method}")
                    await self.method.send[send_method](result.data)

        return flag
