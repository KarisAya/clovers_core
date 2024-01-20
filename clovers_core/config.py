import toml
from pydantic import BaseModel, Extra
from pathlib import Path


class Config(BaseModel, extra=Extra.ignore):
    plugins: list = []

    @classmethod
    def load(cls, path: Path):
        if path.exists():
            env_dict = toml.load(path)
            config = cls.parse_obj(env_dict)
        else:
            path.parent.mkdir(exist_ok=True, parents=True)
            config = cls()
            config.save(path)
        return config

    def save(self, path: Path):
        with open(path, "w") as f:
            toml.dump(self.dict(), f)
