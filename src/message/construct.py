from json import loads
from .header import Header
from .abs.package import Package
from .cam.package import CamPackage
from .denm.package import DenmPackage

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
