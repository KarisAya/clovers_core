import inspect
from collections.abc import Coroutine, Callable

from .plugin import Plugin


class AdapterException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class AdapterMethod:
    def __init__(self) -> None:
        self.kwarg: dict = {}
        self.send: dict = {}

    def get_kwarg(self, method_name: str) -> Callable:
        """添加一个获取参数方法"""

        def decorator(func: Coroutine):
            self.kwarg[method_name] = self.kwfilter(func)

        return decorator

    def send_message(self, method_name: str) -> Callable:
        """添加一个发送消息方法"""

        def decorator(func: Coroutine):
            self.send[method_name] = self.kwfilter(func)

        return decorator

    @staticmethod
    def kwfilter(func: Coroutine):
        kw = inspect.signature(func).parameters.keys()

        async def wrapper(*args, **kwargs):
            return await func(*args, **{k: v for k, v in kwargs.items() if k in kw})

        return wrapper


class Adapter:
    def __init__(self) -> None:
        self.methods: dict[str, AdapterMethod] = {}
        self.main_method: AdapterMethod = AdapterMethod()
        self.plugins: list[Plugin] = []

    async def response(self, adapter: str, command: str, **kwargs) -> int:
        flag = 0
        method = self.methods[adapter]
        for plugin in self.plugins:
            resp = plugin(command)
            for key, event in resp.items():
                handle = plugin.handles[key]
                for k in handle.extra_args:
                    get_kwarg = method.kwarg.get(k) or self.main_method.kwarg.get(k)
                    if not get_kwarg:
                        raise AdapterException(f"使用了未定义的 get_kwarg 方法:{k}")
                    event.kwargs[k] = await get_kwarg(**kwargs)
                result = await handle(event)
                if not result:
                    continue
                flag += 1
                k = result.send_method
                send = method.send.get(k) or self.main_method.send.get(k)
                if not send:
                    raise AdapterException(f"使用了未定义的 send 方法:{k}")
                await send(result.data)

        return flag
