import urllib


def humanize_time(minutes):
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    minutes = minutes
    hours = hours

    duration = []
    if days > 0:
        duration.append('%d day' % days + 's' * (days != 1))
    if hours > 0:
        duration.append('%d hour' % hours + 's' * (hours != 1))
    if minutes > 0:
        duration.append('%d minute' % minutes + 's' * (minutes != 1))
    return ' '.join(duration)


def generate_url(url, parameters):
    return url + '?' + urllib.urlencode(parameters)
