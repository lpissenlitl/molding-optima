from abc import ABC, abstractmethod


class SmsBaseError(Exception):
    pass


class SmsProviderNotSupport(SmsBaseError):
    pass


class SendSMSError(SmsBaseError):
    pass


class SmsProvider(ABC):
    def __init__(self, templates: dict, sign: str, sign_in_front: bool = True):
        """
        :param templates: 短信模板配置，dict结构，key为模板名，value为模板内容,
                模板内容一般需要找短信接入商申请审核通过后才能正常发送.
                模板内容参数占位符必需为 %s 或者 {}。
        :param sign: 短信签名，请找短信接入商申请
        :param sign_in_front: "签名"在短信内容前面。如果为False，则签名在内容后面。
        """
        assert templates
        assert sign

        self.templates = templates
        self.sign = sign
        self.sign_in_front = sign_in_front

    def send(self, phone: str, template_name: str, *placeholders):
        """
        发送单条短信
        :param phone: 手机号，不加国家前缀, 示例：13888888888
        :param template_name: 短信内容模板
        :param placeholders: 模板填充参数
        :return:
        """
        assert placeholders
        content = self._render_content(template_name, *placeholders)
        self.do_send(
            phone, self.sign + content if self.sign_in_front else content + self.sign
        )

    @abstractmethod
    def do_send(self, phone: str, content: str):
        """
        具体接入商实现短信发送逻辑
        """
        pass

    def _render_content(self, template_name, *placeholders):
        """
        根据模板名获取模板，并传入参数渲染输出最终短信内容
        """
        template = self.templates.get(template_name)
        if not template:
            return self._render_without_template(*placeholders)
        if "%s" in template:
            return template % placeholders
        elif "{}" in template:
            return template.format(*placeholders)
        else:
            return template

    @staticmethod
    def _render_without_template(*placeholders):
        return "".join(*placeholders)
