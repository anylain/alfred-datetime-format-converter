# -*- coding: utf-8 -*-

import alfred
import calendar
import re
from datetime import timedelta, datetime
from delorean import utcnow, parse, epoch, utcnow_with_delta


def process(query_str):
    """ Entry point """
    value = parse_query_value(query_str)
    if value is not None:
        results = alfred_items_for_value(value)
        xml = alfred.xml(results)  # compiles the XML answer
        alfred.write(xml)  # writes the XML back to Alfred


def parse_query_value(query_str):
    """ Return value for the query string """
    try:
        query_str = str(query_str).strip('"\' ')
        if query_str.startswith('localnow'):
            d = get_offsetted_time(datetime.now(), query_str)
        elif query_str.startswith('localtoday'):
            d = get_offsetted_time(datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0), query_str)
        elif query_str.startswith('now'):
            d = get_offsetted_time(datetime.utcnow(), query_str)
        elif query_str.startswith('today'):
            d = get_offsetted_time(datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0), query_str)
        elif query_str[0] in ("+", "-"):
            d = get_offsetted_time(datetime.utcnow(), query_str)
        else:
            # Parse datetime string or timestamp
            try:
                ts = float(query_str)
                try:
                    d = epoch(ts)
                except:
                    d = epoch(ts/1000)
            except ValueError:
                d = parse(str(query_str))
    except (TypeError, ValueError):
        d = None
    return d


def get_offsetted_time(dt, query_str):
    m = re.compile(r".*?(?P<action>[\+\-])(?P<policy>.+)").match(query_str)
    if not m:
        return epoch(dt)

    action = m.group("action")
    policy = m.group("policy")

    subPatterns = [
        r"(?:(?P<days>\d+)d)?",
        r"(?:(?P<hours>\d+)h)?",
        r"(?:(?P<minutes>\d+)m)?",
        r"(?:(?P<seconds>\d+)s)?",
    ]
    pattern = "".join(subPatterns)
    pattern = re.compile(pattern, re.I)
    m = pattern.match(policy)
    if m:
        delta_kwargs = {}
        for k, v in m.groupdict().items():
            if v:
                delta_kwargs[k] = int(v)
        delta = timedelta(**delta_kwargs)
        if action == "-":
            delta = -delta
        return epoch(dt + delta)

    return epoch(dt)


def alfred_items_for_value(value):
    """
    Given a delorean datetime object, return a list of
    alfred items for each of the results
    """

    index = 0
    results = []

    # First item as timestamp
    item_value = calendar.timegm(value.datetime.utctimetuple())
    results.append(alfred.Item(
        title=str(item_value),
        subtitle=u'UTC Timestamp',
        attributes={
            'uid': alfred.uid(index),
            'arg': item_value,
        },
        icon='icon.png',
    ))
    index += 1

    # timestamp milliseconds
    item_value = calendar.timegm(value.datetime.utctimetuple())
    results.append(alfred.Item(
        title=str(item_value*1000),
        subtitle=u'UTC Timestamp Milliseconds',
        attributes={
            'uid': alfred.uid(index),
            'arg': item_value*1000,
        },
        icon='icon.png',
    ))
    index += 1

    # Various formats
    formats = [
        # 1937-01-01 12:00:27
        ("%Y-%m-%d %H:%M:%S", ''),
        # 19 May 2002 15:21:36
        ("%d %b %Y %H:%M:%S", ''),
        # Sun, 19 May 2002 15:21:36
        ("%a, %d %b %Y %H:%M:%S", ''),
        # 1937-01-01T12:00:27
        ("%Y-%m-%dT%H:%M:%S", ''),
        # 1996-12-19T16:39:57-0800
        ("%Y-%m-%dT%H:%M:%S%z", ''),
    ]
    for format, description in formats:
        item_value = value.datetime.strftime(format)
        results.append(alfred.Item(
            title=str(item_value),
            subtitle=description,
            attributes={
                'uid': alfred.uid(index),
                'arg': item_value,
            },
            icon='icon.png',
        ))
        index += 1

    return results


if __name__ == "__main__":
    try:
        query_str = alfred.args()[0]
    except IndexError:
        query_str = None
    process(query_str)
