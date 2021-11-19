from json import loads
from src.message.abs.package import Package
from src.message.cam.package import CamPackage
from src.message.denm.package import DenmPackage
from src.message.header import Header

def json_to_package(j_str: str) -> Package: 
    j_dict = loads(j_str)
    if 'header' not in j_dict: raise AttributeError('header')
    if 'body' not in j_dict: raise AttributeError('body')
    head = Header.from_dict(j_dict['header'])
    if head.proto_type == 'CAM': 
        return CamPackage.from_dict(j_dict)
    if head.proto_type == 'DENM': 
        return DenmPackage.from_dict(j_dict)
    raise AttributeError(head.proto_type)
