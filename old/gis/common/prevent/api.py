"""
频率控制器。主要用于接口访问频率限制
"""
import logging

_LOGGER = logging.getLogger(__name__)


class FrequencyLimitService:
    def __init__(self, config, redis):
        self.config = config
        self.redis = redis

    def check(self, code, biz_key, ext_info=""):
        """
        触发一次指定code的规则调用统计, 并返回当前是否已达到策略上限
        :param code: 业务场景编码, 请在配置文件里配置
        :param biz_key: 业务唯一码, 各接入业务模块负责组装, 并保证一个场景code下该值唯一
        :param ext_info: 扩展信息, 用于打印
        :return: 如果触发上限值, 则返回False
        """
        try:
            policy = self.config[code]
            max_timers, period = policy["formula"]
        except KeyError:
            _LOGGER.error("policy code: %s not config" % code)
            return False

        store_key = "fre_{}_{}".format(code, biz_key)
        timers = self.redis.get(store_key)
        timers = int(timers) if timers else 0
        if timers:
            if timers <= max_timers:
                timers = self.redis.incr(store_key)
                if timers == 1:  # 并发控制, 如果刚好过期, 则要重新设置过期时间
                    self.redis.expire(store_key, period)
        else:
            self.redis.set(store_key, 1, ex=period)

        success = timers <= max_timers
        if success:
            _LOGGER.debug(
                "fre check success, code: %s, key: %s, context: %s"
                % (code, biz_key, ext_info)
            )
        else:
            _LOGGER.info(
                "fre check fail, code: %s, key: %s, context: %s"
                % (code, biz_key, ext_info)
            )
        return success

    def clear(self, code, biz_key):
        store_key = "fre_{}_{}".format(code, biz_key)
        self.redis.delete(store_key)
