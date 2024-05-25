from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StatsRequest(_message.Message):
    __slots__ = ("type",)
    TYPE_FIELD_NUMBER: _ClassVar[int]
    type: str
    def __init__(self, type: _Optional[str] = ...) -> None: ...

class StatsItem(_message.Message):
    __slots__ = ("timestamp", "istat1", "istat2", "fstat1", "fstat2")
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    ISTAT1_FIELD_NUMBER: _ClassVar[int]
    ISTAT2_FIELD_NUMBER: _ClassVar[int]
    FSTAT1_FIELD_NUMBER: _ClassVar[int]
    FSTAT2_FIELD_NUMBER: _ClassVar[int]
    timestamp: int
    istat1: int
    istat2: int
    fstat1: float
    fstat2: float
    def __init__(self, timestamp: _Optional[int] = ..., istat1: _Optional[int] = ..., istat2: _Optional[int] = ..., fstat1: _Optional[float] = ..., fstat2: _Optional[float] = ...) -> None: ...

class StatsReply(_message.Message):
    __slots__ = ("stats",)
    class StatsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: StatsItem
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[StatsItem, _Mapping]] = ...) -> None: ...
    STATS_FIELD_NUMBER: _ClassVar[int]
    stats: _containers.MessageMap[str, StatsItem]
    def __init__(self, stats: _Optional[_Mapping[str, StatsItem]] = ...) -> None: ...
