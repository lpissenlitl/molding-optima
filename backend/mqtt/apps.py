from django.apps import AppConfig
import os
from django.conf import settings

class mqttConfig(AppConfig):
    name = 'mqtt'

    def ready(self):
        if settings.MQTT_ENABLED:
            lock_file_path = "/tmp/mqtt_service_lock"
            try:
                # 打开锁文件
                with open(lock_file_path, "w") as lock_file:
                    if os.name == 'posix':
                        import fcntl
                        try:
                            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        except (BlockingIOError, IOError):
                            print("Lock not acquired. Another instance is running.")
                            raise
                    elif os.name == 'nt' and os.environ.get('RUN_MAIN') == 'true':
                        import msvcrt
                        try:
                            # 尝试锁定文件的一部分（Windows 下 locking）
                            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                        except (BlockingIOError, OSError):
                            print("Lock not acquired. Another instance is running.")
                            raise
                    else:
                        print("File locking not supported on this OS.")
                        raise
                    
                    print("Lock acquired. Starting service...")
                    
                    # 启动你的服务
                    from mqtt.services import start_mqtt_service_thread
                    start_mqtt_service_thread()

            except BlockingIOError:
                print("Another instance is already running. Skipping service initialization.")

            except Exception as e:
                print(f"An error occurred: {e}")

            finally:
                try:
                    lock_file.close()
                except:
                    pass