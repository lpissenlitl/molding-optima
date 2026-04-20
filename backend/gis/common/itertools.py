import typing


def batch_preprocessor(
    iterable: typing.Iterable, prepare_func: typing.Callable, batch_size=100, **kwargs
) -> typing.Generator:
    """
    每次从`iterable`中取一批内容出来（每批大小是batch_size），然后先对这一批内容执行`prepare_func`函数。
    :param iterable: 被处理的原始可迭代实例
    :param prepare_func: 预处理函数
    :param batch_size: 每次批处理大小
    :param kwargs: the arguments for `prepare_func`
    :return: return a generator which item is the same as item of the `iterable` instance.
    """
    assert batch_size >= 1
    buffer = list()
    for e in iterable:
        buffer.append(e)
        if len(buffer) >= batch_size:
            prepare_func(buffer, **kwargs)
            for ie in buffer:
                yield ie
            buffer.clear()
