"""Read and write the 9ba626afa44a3aa3.patch_N archive format."""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path

MAGIC = 0xF0000011
TYPE = 0xA14E8DFA2CD117E2
HEADER = struct.Struct('<III20sQQ24s')
TYPE_ENTRY = struct.Struct('<IIQIIII')
RESOURCE = struct.Struct('<7Q6I')


def resource_hash(name: str) -> int:
    data = name.encode('utf-8')
    mask = (1 << 64) - 1
    mix = 0xC6A4A7935BD1E995
    value = len(data) * mix & mask
    end = len(data) // 8 * 8
    for (word,) in struct.iter_unpack('<Q', data[:end]):
        word = word * mix & mask
        word ^= word >> 47
        value = (value ^ (word * mix & mask)) * mix & mask
    if data[end:]:
        value = (value ^ int.from_bytes(data[end:], 'little')) * mix & mask
    value ^= value >> 47
    value = value * mix & mask
    return value ^ (value >> 47)


@dataclass(frozen=True)
class Entry:
    name_hash: int
    type_hash: int
    offset: int
    length: int
    index: int


def entries(data: bytes) -> list[Entry]:
    magic, types, count = struct.unpack_from('<III', data)
    if magic != MAGIC:
        raise ValueError('not a 9ba626afa44a3aa3.patch_N archive')
    table_offset = 72 + types * TYPE_ENTRY.size
    result = []
    for index in range(count):
        fields = RESOURCE.unpack_from(data, table_offset + index * RESOURCE.size)
        name_hash, type_hash, offset, _, _, _, _, length, _, _, _, _, entry_index = fields
        if offset + length > len(data):
            raise ValueError(f'truncated resource {index}: {offset}+{length}>{len(data)}')
        result.append(Entry(name_hash, type_hash, offset, length, entry_index))
    return result


def read_resource(data: bytes, name: str) -> bytes | None:
    key = resource_hash(name)
    for entry in entries(data):
        if entry.name_hash == key:
            return data[entry.offset:entry.offset + entry.length]
    return None


def make_archive(resources: dict[int, bytes]) -> bytes:
    if not resources:
        raise ValueError('archive needs at least one resource')
    count = len(resources)
    offset = (104 + 80 * count + 15) & ~15
    body = bytearray(offset)
    table = bytearray()
    for index, (name_hash, resource) in enumerate(sorted(resources.items())):
        table += RESOURCE.pack(name_hash, TYPE, offset, 0, 0, 0, 0, len(resource), 0, 0, 16, 16, index)
        body += resource
        body += b'\0' * (-len(body) % 16)
        offset = len(body)
    header = HEADER.pack(MAGIC, 1, count, b'', offset, 0, b'')
    type_entry = TYPE_ENTRY.pack(0, 0, TYPE, count, 0, 16, 16)
    body[:104 + len(table)] = header + type_entry + table
    return bytes(body)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def load(path: str | Path) -> bytes:
    return Path(path).read_bytes()


def save(path: str | Path, data: bytes) -> None:
    Path(path).write_bytes(data)
