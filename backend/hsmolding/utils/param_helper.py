from datetime import timedelta, date, datetime
from functools import wraps

day_format = "%Y-%m-%d"


def day_to_str(day):
    return day.strftime(day_format)


def str_to_date(day_str):
    return datetime.strptime(day_str, day_format)


def unfold_days_from_range(start_day, end_day):
    """
    指定开始日期和结束日期，展开返回包含的所有日期字符列表： ['2018-01-02', '2018-01-02']
    :param start_day:
    :param end_day:
    :return:
    """
    result = []
    day = start_day
    while day <= end_day:
        result.append(day.strftime(day_format))
        day = day + timedelta(days=1)
    return result


def parse_order_by_param(order_by):
    if order_by:
        if order_by.startswith("-"):
            order_by = order_by[1:]
            order_direction = -1
        else:
            order_direction = 1
    else:
        order_by = order_by or "day"
        order_direction = -1
    return order_by, order_direction


def float_to_int(input_dic, exclude=list()):
    for key, value in input_dic.items():
        if isinstance(value, float) and key not in exclude:
            input_dic.update({key: int(value)})


def format_rate(input_dic, exclude=list()):
    for key, value in input_dic.items():
        if isinstance(value, float) and key not in exclude:
            if "rate" in key or "ratio" in key:
                input_dic.update({key: round(value, 2)})


def format_data(input_dic, exclude=list()):
    if input_dic and isinstance(input_dic, dict):
        for key, value in input_dic.items():
            if isinstance(value, float) and key not in exclude:
                # if 'rate' in key or 'ratio' in key:
                input_dic.update({key: round(value, 2)})
            # else:
            #     input_dic.update({key: int(value)})
            if isinstance(value, dict) and key not in exclude:
                format_data(value, exclude)


def scale(input_dic, ratio, include=list()):
    if input_dic and isinstance(input_dic, dict):
        for key, value in input_dic.items():
            if isinstance(value, (float, int)) and key in include:
                input_dic.update({key: float("%.2f" % (value * ratio))})
            if isinstance(value, dict) and key in include:
                scale(value, ratio, include)


def check_date_params(start_day, end_day):
    assert isinstance(start_day, date)
    assert isinstance(end_day, date)
    assert start_day <= end_day


def remove_non_ascii(s):
    out = "".join(i for i in s if ord(i) < 128)
    out = out.replace(" ", "")
    return out


def repeat_daily(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_day = args[0]
        end_day = args[1]
        while start_day <= end_day:
            func(start_day, start_day + timedelta(days=1), *args[2:], **kwargs)
            start_day += timedelta(days=1)

    return wrapper


def custom_intersection(lst1, lst2):
    # 返回 None 表示查询时不过滤此条件，为最大集合， 返回 [] 表示最小集合，凡事有[]的查询条件，就表示返回条数为0
    if lst1 is not None and lst2 is not None:
        return [value for value in lst1 if value in lst2]
    elif lst1 is not None:
        return lst1
    elif lst2 is not None:
        return lst2
    else:
        return None
