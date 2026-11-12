from fastapi import APIRouter,Depends
from src.controllers import frame as controller
from src.schemas.entities import FrameInput
from src.services.auth import current,editor
router=APIRouter(prefix='/frames',tags=['frames'])
@router.get('')
def list_items(user=Depends(current)):return controller.list_items()
@router.post('',status_code=201)
def create(data:FrameInput,user=Depends(editor)):return controller.create(data)
