import os
from pathlib import Path
from tempfile import NamedTemporaryFile


def write_immutable(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent) as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
        try:
            os.link(stream.name, path)
        except FileExistsError:
            if path.read_bytes() != content:
                raise ValueError('Published index snapshots are immutable') from None
