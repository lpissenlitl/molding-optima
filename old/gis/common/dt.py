from datetime import datetime, date

from django.utils import timezone


def at_start_of_day(time: datetime) -> datetime:
    """
    获取日期参数'time'的0点开始时间对象。
    :return:
    """
    if not time.tzinfo:
        time = timezone.get_current_timezone().localize(time)

    return time.replace(hour=0, minute=0, second=0, microsecond=0)


def at_start_of_hour(time: datetime) -> datetime:
    """
    获取日期参数`time`当前小时0分开始的时间对象
    """
    if not time.tzinfo:
        time = timezone.get_current_timezone().localize(time)
    return time.replace(minute=0, second=0, microsecond=0)


def date_to_datetime(day: date) -> datetime:
    """
    convert date to datetime with current timezone
    """
    return timezone.get_current_timezone().localize(
        datetime.combine(day, datetime.min.time())
    )
