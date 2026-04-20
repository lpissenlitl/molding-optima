from mdprocess.models import ProcessIndex
from mdprocess.dao.process_record_model import ProcessParameterRecordDoc
from mdprocess.services import process_index_service
from hsmolding.exceptions import ERROR_DATA_NOT_EXIST
from gis.common.exceptions import BizException
error_message = ""


# 获取有效工艺记录
def get_process_record(process_index_id):
    record = ProcessParameterRecordDoc.objects.filter(process_index_id=process_index_id).first()
    if record:
        return record.to_dict() if record else None
    else:
        raise BizException(ERROR_DATA_NOT_EXIST)


# 添加工艺优化记录
def add_process_record(params: dict):
    record = ProcessParameterRecordDoc.objects.filter(process_index_id=params.get("process_index_id")).first()
    if not record:
        record = ProcessParameterRecordDoc(**params)
        record.save()
    return record.to_dict() if record else None


# 更新工艺优化记录
def update_process_record(params: dict):
    process_index_id = params.get("process_index_id")
    update_process_index(params)
    if process_index_id:
        record = ProcessParameterRecordDoc.objects.filter(process_index_id=process_index_id).first()
        if record:
            record.update(**params)
            return record
        else:
            raise BizException(ERROR_DATA_NOT_EXIST)
    else:
        return None
        

# 删除工艺优化记录
def delete_process_record(process_index_id):
    process = ProcessIndex.objects.filter(id=process_index_id).first()
    if process:
        process.delete()
    else:
        raise BizException(ERROR_DATA_NOT_EXIST)
    record = ProcessParameterRecordDoc.objects.filter(process_index_id=process_index_id).first()
    if record:
        record.delete()
    else:
        raise BizException(ERROR_DATA_NOT_EXIST)


def update_process_index(params):
    process_index = params.get("precondition")
    process_index_service.update_process_index(params.get("process_index_id"),process_index)