from typing import *
from pydantic import BaseModel, Field

class Entry(BaseModel):
    relative_path: str
    modified_time: str
    created_by: str
    modified_by: str
    size: float
    url: str
    result: str

class EntrySimple(BaseModel):
    relative_path: str
    url: str
    child: list = []

class ListRequest(BaseModel):
    url: str

class ConvertRequest(BaseModel):
    url: str
    fbx_path: str

class ConvertResponse(BaseModel):
    url: str
    usd_path: str
    result: str

class SaveRequest(BaseModel):
    usd_path: str
    materials_data: dict
    url: str

class ListResponse(BaseModel):
    this_entry: Entry
    entries: list = [EntrySimple]

class SaveResponse(BaseModel):
    usd_path: str
    url: str
    result: str

class MaterialsResponse(BaseModel):
    materials_data: dict

class ErrorResponse(BaseModel):
    info: str

class LockResponse(BaseModel):
    url: str
    result: str
    