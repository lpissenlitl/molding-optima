from opcua import Client, Node, ua
import os
import paho.mqtt.client as mqtt
import time
import logging

opc_client = None

label_map = {
    "barrel_temperature_stage": "ns=4;s=APPL.HeatingNozzle1.sv_iNumberOfZones",  # 温度段数
    "NT": "ns=4;s=APPL.HeatingNozzle1.sv_ZoneRetain1.rSetValVis",  # 温度段一
    "BT1": "ns=4;s=APPL.HeatingNozzle1.sv_ZoneRetain2.rSetValVis",  # 温度段二
    "BT2": "ns=4;s=APPL.HeatingNozzle1.sv_ZoneRetain3.rSetValVis",  # 温度段三
    "BT3": "ns=4;s=APPL.HeatingNozzle1.sv_ZoneRetain4.rSetValVis",  # 温度段四
    "BT4": "ns=4;s=APPL.HeatingNozzle1.sv_ZoneRetain5.rSetValVis",  # 温度段五
    "BT5": "ns=4;s=APPL.HeatingNozzle1.sv_ZoneRetain6.rSetValVis",  # 温度段六
    "BT6": "ns=4;s=APPL.HeatingNozzle1.sv_ZoneRetain7.rSetValVis",  # 温度段七
    "injection_stage": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.iNoOfPoints",  # 注射段数
    "IP0": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[1].rPressure",  # 注射一段压力
    "IP1": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[2].rPressure",  # 注射二段压力
    "IP2": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[3].rPressure",  # 注射三段压力
    "IP3": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[4].rPressure",  # 注射四段压力
    "IP4": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[5].rPressure",  # 注射五段压力
    "IP5": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[6].rPressure",  # 注射六段压力
    "IV0": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[1].rVelocity",  # 注射一段速度
    "IV1": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[2].rVelocity",  # 注射二段速度
    "IV2": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[3].rVelocity",  # 注射三段速度
    "IV3": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[4].rVelocity",  # 注射四段速度
    "IV4": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[5].rVelocity",  # 注射五段速度
    "IV5": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[6].rVelocity",  # 注射六段速度
    "IL0": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[2].rStartPos",  # 注射一段位置
    "IL1": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[3].rStartPos",  # 注射二段位置
    "IL2": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[4].rStartPos",  # 注射三段位置
    "IL3": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[5].rStartPos",  # 注射四段位置
    "IL4": "ns=4;s=APPL.Injection1.sv_InjectProfVis.Profile.Points[6].rStartPos",  # 注射五段位置
    "VPTL": "ns=4;s=APPL.Injection1.sv_CutOffParams.rPositionThreshold",  # 位置切保压
    "VPTT": "ns=4;s=APPL.Injection1.sv_CutOffParams.dTimeThreshold",  # 时间切保压
    "holding_stage": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.iNoOfPoints",  # 保压段数
    "PP0": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[1].rPressure",  # 保压一段压力
    "PP1": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[2].rPressure",  # 保压二段压力
    "PP2": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[3].rPressure",  # 保压三段压力
    "PP3": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[4].rPressure",  # 保压四段压力
    "PP4": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[5].rPressure",  # 保压五段压力
    "PV0": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[1].rVelocity",  # 保压一段速度
    "PV1": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[2].rVelocity",  # 保压二段速度
    "PV2": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[3].rVelocity",  # 保压三段速度
    "PV3": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[4].rVelocity",  # 保压四段速度
    "PV4": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[5].rVelocity",  # 保压五段速度
    "PT0": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[2].rStartPos",  # 保压一段时间
    "PT1": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[3].rStartPos",  # 保压二段时间
    "PT2": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[4].rStartPos",  # 保压三段时间
    "PT3": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[5].rStartPos",  # 保压四段时间
    "PT4": "ns=4;s=APPL.Injection1.sv_HoldProfVis.Profile.Points[6].rStartPos",  # 保压五段时间
    "CT": "ns=4;s=APPL.CoolingTime1.sv_dCoolingTime",  # 设定冷却时间
    "metering_stage": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.iNoOfPoints",  # 熔胶段数
    "MD": "ns=4;s=APPL.Injection1.sv_PlastTimesSet.dSetDelayTime",  # 熔胶延时
    "MSR0": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[1].rRotation",  # 熔胶一段转速
    "MSR1": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[2].rRotation",  # 熔胶二段转速
    "MSR2": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[3].rRotation",  # 熔胶三段转速
    "MSR3": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[4].rRotation",  # 熔胶四段转速
    "MBP0": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[1].rBackPressure",  # 熔胶一段背压
    "MBP1": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[2].rBackPressure",  # 熔胶二段背压
    "MBP2": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[3].rBackPressure",  # 熔胶三段背压
    "MBP3": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[4].rBackPressure",  # 熔胶四段背压
    "ML0": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[2].rStartPos",  # 熔胶一段位置
    "ML1": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[3].rStartPos",  # 熔胶二段位置
    "ML2": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[4].rStartPos",  # 熔胶三段位置
    "ML3": "ns=4;s=APPL.Injection1.sv_PlastProfVis.Profile.Points[5].rStartPos",  # 熔胶四段位置
    "DPBM": "ns=4;s=APPL.Injection1.sv_DecompBefPlastSettings.ConstOutput.Pressure.Output.rOutputValue",  # 熔胶前松退压力
    "DVBM": "ns=4;s=APPL.Injection1.sv_DecompBefPlastSettings.ConstOutput.Velocity.Output.rOutputValue",  # 熔胶前松退速度
    "DDBM": "ns=4;s=APPL.Injection1.sv_DecompBefPlastSettings.rDecompPos",  # 熔胶前松退位置
    "DTBM": "ns=4;s=APPL.Injection1.sv_DecompBefPlastSettings.dDecompTime",  # 熔胶前松退时间
    "DPAM": "ns=4;s=APPL.Injection1.sv_DecompAftPlastSettings.ConstOutput.Pressure.Output.rOutputValue",  # 熔胶后松退压力
    "DVAM": "ns=4;s=APPL.Injection1.sv_DecompAftPlastSettings.ConstOutput.Velocity.Output.rOutputValue",  # 熔胶后松退速度
    "DDAM": "ns=4;s=APPL.Injection1.sv_DecompAftPlastSettings.rDecompPos",  # 熔胶后松退位置
    "DTAM": "ns=4;s=APPL.Injection1.sv_DecompAftPlastSettings.dDecompTime"  # 熔胶后松退时间
}

# MQTT协议订阅数据所需
def on_connect(client, userdata, flags, rc):
    pass


def on_message(client, userdata, msg):
    params: dict = eval(msg.payload.decode('gb2312'))
    if params.get("type") == "write" and params.get("process"):
        opc_client.write_machine_process(params.get("process"))
    elif params.get("type") == "read":
        opc_client.data_publish(str(opc_client.read_machine_process()))


class OpcComClient():

    def __init__(self):
        self.server_url = "opc.tcp://192.168.23.43:4842"
        self.opc_client = None
        self.node_map = None

        self.mqtt_host = "159.75.135.188"
        self.mqtt_port = 1883
        self.mqtt_client = None
        self.mqtt_topic = "opc_yizumi"


    def connectToServer(self, url: str):
        try:
            self.server_url = url
            self.opc_client = Client(self.server_url)
            self.init_node_map(label_map)
            return 0
        except:
            pass


    def init_node_map(self, label_map: dict):
        self.node_map = {}
        for key, value in label_map.items():
            self.node_map[key] = self.opc_client.get_node(value)


    def read_machine_process(self):
        process_data = {}
        for key, node in self.node_map.items():
            process_data[key] = node.get_value()
        return process_data


    def write_machine_process(self, process_data: dict):
        # 写入数据
        for key, value in process_data.items():
            if not value:
                continue
            if key in ["injection_stage", "holding_stage", "metering_stage", "barrel_temperature_stage"]:
                val = ua.DataValue(ua.Variant(value, ua.VariantType.UInt32))
                self.node_map[key].set_value(val)
            elif key in ["IP0", "IP1", "IP2", "IP3", "IP4", "IP5", "PP0", "PP1", "PP2", "PP3", "PP4", "MBP0", "MBP1",
                         "MBP2", "MBP3", "DPBM", "DPAM"]:
                val = ua.DataValue(ua.Variant(process_data.get(key), ua.VariantType.Float))
                self.node_map[key].set_value(val)
            elif key in ["IV0", "IV1", "IV2", "IV3", "IV4", "IV5", "PV0", "PV1", "PV2", "PV3", "DVBM", "DVAM"]:
                val = ua.DataValue(ua.Variant(process_data.get(key), ua.VariantType.Float))
                self.node_map[key].set_value(val)
            elif key in ["IL0", "IL1", "IL2", "IL3", "IL4", "IL5"]:
                val = ua.DataValue(ua.Variant(process_data.get(key) / 1.04, ua.VariantType.Float))
                self.node_map[key].set_value(val)
            else:
                val = ua.DataValue(ua.Variant(process_data.get(key), ua.VariantType.Float))
                self.node_map[key].set_value(val)


    def start_mqtt_service(self):
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_message = on_message


    def data_publish(self, msg: str):
        self.mqtt_client.publish(self.mqtt_topic, msg, 0, True)


    def data_subscribe(self, topic: str):
        self.mqtt_client.subscribe(topic, 0)


if __name__ == "__main__":
    opc_client = OpcComClient()
    opc_client.start_mqtt_service()
    opc_client.data_subscribe("Yizumi")
    opc_client.mqtt_client.loop_forever()