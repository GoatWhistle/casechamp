from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pyarrow as pa
from pyarrow import ipc


def stream_batches(client, sql, parameters):
    query = urlencode(
        {
            "readonly": 2,
            "max_execution_time": 300,
            **{"param_" + key: value for key, value in parameters.items()},
        }
    )
    request = Request(
        client.url.geturl() + "/?" + query,
        data=(sql + " FORMAT ArrowStream").encode(),
        headers=client.headers,
    )
    with urlopen(request, timeout=330) as response:
        yield from ipc.open_stream(pa.input_stream(response))
