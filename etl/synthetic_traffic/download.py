import os
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen


class RangeUnavailable(Exception):
    pass


def download(url: str, destination: Path, workers: int = 4) -> str:
    headers = {"User-Agent": "Plexus public data collection"}
    with urlopen(Request(url, headers=headers, method="HEAD"), timeout=60) as response:
        size = int(response.headers.get("Content-Length") or 0)
        etag = response.headers.get("ETag")
    if size > 0 and etag:
        try:
            with destination.open("wb") as stream:
                stream.truncate(size)
                descriptor = stream.fileno()

                def part(start: int) -> None:
                    end = min(size, start + 32 * 1024 * 1024) - 1
                    request = Request(
                        url,
                        headers={
                            **headers,
                            "Range": f"bytes={start}-{end}",
                            "If-Match": etag,
                        },
                    )
                    with urlopen(request, timeout=60) as response:
                        if (
                            response.status != 206
                            or response.headers.get("Content-Range")
                            != f"bytes {start}-{end}/{size}"
                        ):
                            raise RangeUnavailable()
                        position = start
                        while block := response.read(
                            min(1024 * 1024, end - position + 1)
                        ):
                            remaining = memoryview(block)
                            while remaining:
                                count = os.pwrite(descriptor, remaining, position)
                                position += count
                                remaining = remaining[count:]
                            if position > end:
                                break
                        if position != end + 1:
                            raise ValueError("Incomplete download range")

                with ThreadPoolExecutor(max_workers=workers) as executor:
                    list(executor.map(part, range(0, size, 32 * 1024 * 1024)))
        except RangeUnavailable:
            size = 0
    else:
        size = 0
    if size == 0:
        with (
            urlopen(Request(url, headers=headers), timeout=60) as response,
            destination.open("wb") as stream,
        ):
            while block := response.read(1024 * 1024):
                stream.write(block)
    digest = sha256()
    with destination.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()
