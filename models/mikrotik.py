from pydantic import BaseModel, ConfigDict


def to_sneak(string: str) -> str:
    return string.replace('-', '_')


class Script(BaseModel):
    model_config = ConfigDict(alias_generator=to_sneak)
    id: int
    name: str
    owner: str
    policy: str
    dont_require_permissions: str
    run_count: int
    source: str
    invalid: str
