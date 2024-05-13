import omni.kit.asset_converter as converter
import omni.client
from omni.services.core import routers
import carb
from typing import Optional
from pydantic import BaseModel, Field
from .model import *
import os
import json
import asyncio

from pxr import Usd, UsdShade

router = routers.ServiceAPIRouter()

@router.post(path="/list")
async def get_list(item: ListRequest):

    def convert2(entries, _url):
        entries_model = []
        for entry in entries:
            entries_model.append(EntrySimple(
                relative_path=entry.relative_path,
                url=_url + entry.relative_path, 
                child=[]))
        return entries_model
    

    url = item.url
    __url = f"omniverse://{url}"
    res, parent_entry = await omni.client.stat_async(__url)

    if res == omni.client.Result.ERROR_CONNECTION:
        return ErrorResponse(info=res.name)
    
    _, entries = await omni.client.list_async(__url)
    # print(result) # omni.client.Result.OK)

    this_entry = Entry(
        relative_path=parent_entry.relative_path,
        modified_time=str(parent_entry.modified_time),
        created_by=str(parent_entry.created_by),
        modified_by=str(parent_entry.modified_by),
        size=parent_entry.size,
        url=url,
        result=res.name)

    entries_models = []

    for entry in entries:
        url = f"{item.url}/{entry.relative_path}/"
        _url = "omniverse://" + url
        print(url)
        _, _entries = await omni.client.list_async(_url)
        entries_models.append(EntrySimple(
            relative_path=entry.relative_path,
            url=url, 
            child=convert2(_entries, url)))

    return ListResponse(this_entry=this_entry, entries=entries_models)

@router.post(path="/stat")
async def get_stat(item: ListRequest):
    url = item.url
    __url = f"omniverse://{url}"
    _, entry = await omni.client.stat_async(__url)

    if _ == omni.client.Result.ERROR_CONNECTION:
        return ErrorResponse(info=_.name)
    
    this_entry = Entry(
        relative_path=entry.relative_path,
        modified_time=str(entry.modified_time),
        created_by=str(entry.created_by),
        modified_by=str(entry.modified_by),
        size=entry.size,
        url=url,
        result=_.name)
    
    return this_entry



@router.post(path="/lock")
async def lock(item: ListRequest):
    future = asyncio.get_event_loop().create_future()

    def lock_callback(result):
        print(result.name)
        future.set_result(LockResponse(url=item.url, result=result.name))

    url = item.url
    __url = f"omniverse://{url}"
    omni.client.lock_with_callback(__url, lock_callback)

    return await future

@router.post(path="/unlock")
async def unlock(item: ListRequest):
    future = asyncio.get_event_loop().create_future()

    def unlock_callback(result):
        print(result.name)
        future.set_result(LockResponse(url=item.url, result=result.name))

    url = item.url
    __url = f"omniverse://{url}"
    omni.client.unlock_with_callback(__url, unlock_callback)

    return await future


@router.post(path="/convert")
async def convert(item: ConvertRequest):

    def progress_callback(current_step: int, total: int):
        pass

    input_asset_path = item.fbx_path
    file_name = os.path.splitext(input_asset_path)[0]
    output_asset_path = file_name + ".usd"

    task_manager = converter.get_instance()
    task = task_manager.create_converter_task(input_asset_path, output_asset_path, progress_callback)
    success = await task.wait_until_finished()
    if not success:
        detailed_status_code = task.get_status()
        detailed_status_error_string = task.get_error_message()
        return ConvertResponse(url=item.url, usd_path=output_asset_path, result=detailed_status_error_string)
    
    return ConvertResponse(url=item.url, usd_path=output_asset_path, result="OK")

@router.post(path="/save")
async def save(item: SaveRequest):

    url = item.url
    __url = f"omniverse://{url}"

    output_asset_path = item.usd_path
    # print(__url)
    with open(output_asset_path, "rb") as f:
        content = f.read()
    result = await omni.client.write_file_async(__url, content)

    ovmt_url = url.replace(".usd", ".ovmt")
    mat_url = f"omniverse://{ovmt_url}"

    materials_data = item.materials_data
    material_content = json.dumps(materials_data).encode("utf-8")
    await omni.client.write_file_async(mat_url, material_content)

    return SaveResponse(usd_path=output_asset_path, url=url, result=result.name)

@router.post(path="/material")
async def get_material(item: ListRequest):

    def get_children_paths(stage, parent_path):
        parent_prim = stage.GetPrimAtPath(parent_path)
        return [child.GetPrimPath() for child in parent_prim.GetAllChildren()]

    def get_bound_object_names(stage, material_path):
        # stage = omni.usd.get_context().get_stage()
        material_prim_obj = stage.GetPrimAtPath(material_path)

        prim_names = []
        stage_prims = list(stage.Traverse())
        bounds = UsdShade.MaterialBindingAPI.ComputeBoundMaterials(stage_prims, UsdShade.Tokens.allPurpose)
        for stage_prim, material, relationship in zip(stage_prims, bounds[0], bounds[1]):
            material_prim = material.GetPrim()
            if not material_prim.IsValid():
                continue
            
            if material_prim.GetPrimPath() != material_path:
                continue
                
            prim_names.append(stage_prim.GetName())

        material_name = material_prim_obj.GetName()

        return material_name, prim_names
        
    url = item.url
    __url = f"omniverse://{url}"
    stage_ref = Usd.Stage.Open(__url)

    paths = []
    for prim_ref in stage_ref.Traverse():
        paths.append(str(prim_ref.GetPath()))

    looks = []
    for prim_ref in stage_ref.Traverse():
        p = str(prim_ref.GetPath())
        if p.endswith("Looks"):
            looks.append(p)
    
    material_paths = []
    for look_path in looks:
        material_paths += get_children_paths(stage_ref, look_path)

    material_data = {}
    for material_path in material_paths:
        material_name, bound_objs = get_bound_object_names(stage_ref, material_path)  # get the material binding objects
        if len(bound_objs) != 0:
            material_data[material_name] = bound_objs

    return MaterialsResponse(materials_data=material_data)
