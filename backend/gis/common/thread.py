"""
参考 java 中 RejectedExecutionHandler 实现方式，加强 ThreadPoolExecutor 功能，
因为自带的实现中，提交的任务都是会有queue中排队执行，但是当大量任务积压时，整个系统
可用性其实已经很低了，所以控制后续任务拒绝方式很有必要。

Note: 在uwsgi + django 模式下最好不要使用线程异步处理，因为uwsgi会在某些场景下kill当前
进程（比如max-requests, harakiri配置都会引起进程被kill）,这样当前进程下启动的线程都会
结束掉。建议使用 Celery 相关线下异步任务组件。
"""
import logging
import signal
import threading
import time
import typing
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum, auto

_LOGGER = logging.getLogger(__name__)


class ThreadPoolExecutorPolicy(Enum):
    """
    任务队列满时，后续提交任务拒绝策略
    """

    # 等待队列有空的资源
    WaitPolicy = auto()
    # 拒绝接收任务，直接抛错
    AbortPolicy = auto()
    # 由当前调用线程直接执行
    CallerRunsPolicy = auto()


class RejectedExecutionException(Exception):
    pass


class BoundedThreadPoolExecutor:
    def __init__(self, bound, policy, max_workers=None, thread_name_prefix=""):
        self._bound = bound
        self._policy = policy
        self._executor = ThreadPoolExecutor(max_workers, thread_name_prefix)
        self._semaphore = threading.BoundedSemaphore(bound)

    def submit(self, fn, *args, **kwargs):
        running = self._semaphore.acquire(blocking=False)
        if not running:
            if self._policy == ThreadPoolExecutorPolicy.WaitPolicy:
                self._semaphore.acquire()
            elif self._policy == ThreadPoolExecutorPolicy.AbortPolicy:
                raise RejectedExecutionException(
                    "current threads count greater {}".format(self._bound)
                )
            elif self._policy == ThreadPoolExecutorPolicy.CallerRunsPolicy:
                feature = Future()
                try:
                    result = fn(*args, **kwargs)
                except BaseException as exc:
                    feature.set_exception(exc)
                else:
                    feature.set_result(result)
                return feature

        try:
            feature = self._executor.submit(fn, *args, **kwargs)
        except Exception:
            self._semaphore.release()
            raise
        else:
            feature.add_done_callback(lambda x: self._semaphore.release())
        return feature

    def shutdown(self, wait=True):
        self._executor.shutdown(wait)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)
        return False


class ServiceExit(Exception):
    pass


class Thread(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self._shutdown_flag = threading.Event()

    def is_shut_down(self) -> bool:
        return self._shutdown_flag.is_set()

    def shut_down(self):
        self._shutdown_flag.set()


class GracefulExitedExecutor:
    def __init__(self, group_name: str, tasks: typing.Sequence[Thread]):
        self.group_name = group_name
        self.tasks = tasks
        signal.signal(signal.SIGTERM, self.service_shutdown)
        signal.signal(signal.SIGINT, self.service_shutdown)

    def start(self):
        _LOGGER.error("the task group [%s] is starting" % self.group_name)
        try:
            for t in self.tasks:
                t.start()

            while True:
                for t in self.tasks:
                    if not t.isAlive():
                        _LOGGER.info(
                            "the task in group is died: thread: [{}] in group: [{}] ...".format(
                                t, self.group_name
                            )
                        )
                        raise ServiceExit()
                time.sleep(1)
        except ServiceExit:
            for t in self.tasks:
                t.shut_down()
            for t in self.tasks:
                t.join()
        _LOGGER.error("the task group is exited, group name: [%s]" % self.group_name)

    def service_shutdown(self, signum, frame):
        raise ServiceExit
