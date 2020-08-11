import requests


def stream_file(file_url, chunk_size):
    response = requests.get(file_url, stream=True)
    yield from response.iter_content(chunk_size=chunk_size)


def human_readable_size(size, divider=1024):
    """
    >>> human_readable_size(100)
    '100B'
    >>> human_readable_size(1023)
    '1023B'
    >>> human_readable_size(1024)
    '1kB'
    >>> human_readable_size(1.5 * 1024)
    '1.50kB'
    >>> human_readable_size(1024 * 1024)
    '1MB'
    >>> human_readable_size(1024 * 1024 * 1024)
    '1GB'
    >>> human_readable_size(1024 * 1024 * 1024 * 1024)
    '1TB'
    >>> human_readable_size(1024 * 1024 * 1024 * 1024 * 1024)
    '1PB'
    >>> human_readable_size(1024 * 1024 * 1024 * 1024 * 1024 * 1024)
    '1EB'
    >>> human_readable_size(1024 * 1024 * 1024 * 1024 * 1024 * 1024 * 1024)
    '1024EB'
    """

    multipliers = list("kMGTPE")
    multiplier = ""
    while size >= divider and multipliers:
        size /= divider
        multiplier = multipliers.pop(0)
    if size - int(size) > 0:
        return f"{size:4.2f}{multiplier}B".strip()
    else:
        return f"{int(size):4}{multiplier}B".strip()
