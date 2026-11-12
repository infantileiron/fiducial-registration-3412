from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
class InputModel(BaseModel):
 model_config=ConfigDict(allow_inf_nan=False)
class LoginInput(InputModel):
 email:str
 password:str
class DatasetInput(InputModel):
 name:str=Field(min_length=2,max_length=100)
 source:str=Field(default='haochuan_fiducials_202611.csv',max_length=100)
 csv_text:str=Field(min_length=10,max_length=350000)
class RenameDataset(InputModel):
 name:str=Field(min_length=2,max_length=100)
class FrameInput(InputModel):
 name:str=Field(min_length=2,max_length=100)
 dataset_id:str
 source_frame:str=Field(default='CAMERA-A',min_length=1,max_length=50)
 target_frame:str=Field(default='TABLE-B',min_length=1,max_length=50)
 unit:Literal['mm']='mm'
 axes:Literal['right-handed xyz']='right-handed xyz'
class RegistrationStudyInput(InputModel):
 name:str=Field(min_length=2,max_length=100)
 dataset_id:str
 frame_id:str
 threshold_mm:float=Field(default=.5,ge=.000001,le=100)
 iterations:int=Field(default=400,ge=1,le=2000)
 seed:int=Field(default=2405,ge=0,le=2147483647)
class RunInput(InputModel):
 study_id:str
class ReviewInput(InputModel):
 run_id:str
 comment:str=Field(min_length=5,max_length=2000)
class DecisionInput(InputModel):
 status:Literal['approved','rejected']
 comment:str=Field(min_length=5,max_length=2000)
class ReportInput(InputModel):
 run_id:str
 review_id:str
 title:str=Field(min_length=2,max_length=100)
