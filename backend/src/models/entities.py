from dataclasses import dataclass,field
from typing import Any
@dataclass
class FiducialDataset:
 id:str
 name:str
 source:str
 points:list[dict]
 created_at:str=''
@dataclass
class FrameSpec:
 id:str
 name:str
 dataset_id:str
 source_frame:str
 target_frame:str
 unit:str
 axes:str
 created_at:str=''
@dataclass
class RegistrationStudy:
 id:str
 name:str
 dataset_id:str
 frame_id:str
 threshold_mm:float
 iterations:int
 seed:int
 snapshot:dict
 checksum:str
 created_at:str=''
@dataclass
class RegistrationRun:
 id:str
 study_id:str
 status:str='queued'
 result:dict[str,Any]=field(default_factory=dict)
 error:str=''
 created_at:str=''
@dataclass
class AlignmentReview:
 id:str
 run_id:str
 comment:str
 status:str='pending'
 reviewer:str=''
 created_at:str=''
@dataclass
class Report:
 id:str
 run_id:str
 review_id:str
 title:str
 created_at:str=''
