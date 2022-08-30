from dataclasses import Field, dataclass, fields
from typing import Any, Protocol, Type


@dataclass(frozen=True, eq=True)
class Model:
    id: int
    dupa: str


@dataclass(frozen=True, eq=True)
class TestModel:
    id: int
    dupa: str


print(hash(Model))

print(hash(TestModel))


class HashableField:
    name: str
    type: Type

    def __init__(self, field: Field):
        self.name = field.name
        self.type = field.type

    def __eq__(self, o: object) -> bool:
        match o:
            case HashableField(name=n, type=t):
                return self.name == n and self.type == t
            case _:
                return False

    def __str__(self) -> str:
        return f"{self.name}: {self.type.__name__}"

    def __hash__(self) -> int:
        return hash(repr(self))

    def __repr__(self) -> str:
        return f"{self.name!r} ({self.type!r})"


class Dataclass(Protocol):
    __dataclass_fields__: dict[str, Any]


def diff_dataclasses(base: Dataclass, other: Dataclass):
    base_fields = {HashableField(field) for field in fields(base)}
    other_fields = {HashableField(field) for field in fields(other)}
    return base_fields, other_fields, base_fields & other_fields


a, b, c = diff_dataclasses(Model, TestModel)

print(list(map(str, c)))
