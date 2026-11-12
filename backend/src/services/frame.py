from src.models.entities import FrameSpec
from src.utils import repository as repo
from src.utils.identity import new_id,now
def list_frames():return repo.all_rows('frames')
def create(data):
 repo.get('datasets',data.dataset_id)
 if not data.source_frame.strip() or not data.target_frame.strip():raise ValueError('轴系名称不能全为空白')
 if data.source_frame.strip()==data.target_frame.strip():raise ValueError('源与目标轴系名称应不同，避免方向混淆')
 return repo.put('frames',FrameSpec(new_id('frame'),data.name,data.dataset_id,data.source_frame.strip(),data.target_frame.strip(),data.unit,data.axes,now()))
