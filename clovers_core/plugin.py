import importlib
import importlib.util
import re
from collections.abc import Callable


class PluginException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Result:
    def __init__(self, send_method: str, data) -> None:
        self.send_method = send_method
        self.data = data


class Event:
    def __init__(
        self,
        raw_command: str,
        args: list = [],
    ):
        self.raw_command = raw_command
        self.args = args
        self.kwargs = {}


class Handle:
    def __init__(
        self,
        commands: set[str] | re.Pattern,
        extra_args: set[str],
    ):
        self.commands = commands
        self.extra_args: set[str] = extra_args
        """
        需要额外的参数
            "avatar":头像url
            "group_info":群头像url,群名
            "permission":权限等级
                用户：0
                群管：1
                群主：2
                超管：3
            "image_list":图片url
            "to_me":bool
            "at":list
        """

    @staticmethod
    async def func(event: Event) -> Result:
        pass

    async def __call__(self, event: Event) -> Result:
        return await self.func(event)


class Plugin:
    def __init__(self, name: str = "") -> None:
        self.name: str = name
        self.handles: dict[int, Handle] = {}
        self.command_dict: dict[str, set[int]] = {}
        self.regex_dict: dict[re.Pattern, set[int]] = {}
        self.got_dict: dict = {}

    def handle(
        self,
        commands: str | set[str] | re.Pattern,
        extra_args: set[str] = set(),
    ):
        def decorator(func: Callable):
            key = len(self.handles)
            if isinstance(commands, str):
                self.command_dict.setdefault(commands, set()).add(key)
            elif isinstance(commands, set):
                for command in commands:
                    self.command_dict.setdefault(command, set()).add(key)
            elif isinstance(commands, re.Pattern):
                self.regex_dict.setdefault(command, set()).add(key)
            else:
                raise PluginException(f"指令：{commands} 类型错误：{type(commands)}")

            handle = Handle(commands, extra_args)

            async def wrapper(event: Event):
                result = await func(event)
                return result

            handle.func = wrapper
            self.handles[key] = handle

        return decorator

    @staticmethod
    def load(name: str, path: str = None):
        print(f"【loading plugin】 {name} ...")
        try:
            if path:
                spec = importlib.util.spec_from_file_location("custom_module", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                module = importlib.import_module(name)
            plugin = module.__plugin__
            print("\tSuccess !")
            return plugin
        except Exception as e:
            print(f"\tFail:{e}")
            return

    def command_check(self, command: str) -> dict[int, Event]:
        if not (command_list := command.strip().split()):
            return
        command_start = command_list[0]
        kv = {}
        for cmd, keys in self.command_dict.items():
            if not command_start.startswith(cmd):
                continue
            if command_start == cmd:
                args = command_list[1:]
            else:
                command_list[0] = command_list[0][len(cmd) :]
                args = command_list
            for key in keys:
                kv[key] = Event(command, args)

        return kv

    def __call__(self, command: str) -> dict[int, Event]:
        kv = {}
        kv.update(self.command_check(command))
        return kv
