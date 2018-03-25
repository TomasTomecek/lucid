from datetime import datetime


def humanize_bytes(bytesize, precision=2):
    """
    Humanize byte size figures
    https://gist.github.com/moird/3684595
    """
    abbrevs = (
        (1 << 50, 'PB'),
        (1 << 40, 'TB'),
        (1 << 30, 'GB'),
        (1 << 20, 'MB'),
        (1 << 10, 'kB'),
        (1, 'bytes')
    )
    if bytesize == 1:
        return '1 byte'
    factor, suffix = 1, "bytes"
    for factor, suffix in abbrevs:
        if bytesize >= factor:
            break
    if factor == 1:
        precision = 0
    return '%.*f %s' % (precision, bytesize / float(factor), suffix)


def humanize_time(value):
    abbrevs = (
        (1, "now"),
        (2, "{seconds} seconds ago"),
        (59, "{seconds} seconds ago"),
        (60, "{minutes} minute ago"),
        (119, "{minutes} minute ago"),
        (120, "{minutes} minutes ago"),
        (3599, "{minutes} minutes ago"),
        (3600, "{hours} hour ago"),
        (7199, "{hours} hour ago"),
        (86399, "{hours} hours ago"),
        (86400, "{days} day ago"),
        (172799, "{days} day ago"),
        (172800, "{days} days ago"),
        (172800, "{days} days ago"),
        (2591999, "{days} days ago"),
        (2592000, "{months} month ago"),
        (5183999, "{months} month ago"),
        (5184000, "{months} months ago"),
    )
    n = datetime.now()
    delta = n - value
    guard, message = 1, "now"
    for guard, message in abbrevs:
        s = int(delta.total_seconds())
        if guard >= s:
            break
    return message.format(seconds=delta.seconds, minutes=int(delta.seconds // 60),
                          hours=int(delta.seconds // 3600), days=delta.days,
                          months=int(delta.days // 30))
