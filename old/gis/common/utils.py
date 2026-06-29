import user_agents


def get_request_ip(request):
    if "HTTP_X_FORWARDED_FOR" in request.META.keys():
        ip = request.META["HTTP_X_FORWARDED_FOR"]
    else:
        ip = request.META["REMOTE_ADDR"]

    return ip


def get_request_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "")


def shorten_user_agent(ua_str):
    user_agent = user_agents.parse(ua_str)
    if user_agent.device.family == "iOS-Device":
        device = "iPhone"
    else:
        device = user_agent.device.family
    return device + "| " + user_agent.os.family + " " + user_agent.os.version_string
