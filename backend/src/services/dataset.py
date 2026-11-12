from src.models.entities import FiducialDataset
from src.services.points import parse_points
from src.utils import repository as repo
from src.utils.identity import new_id,now
def list_datasets():return [{k:v for k,v in d.items() if k!='points'}|{'point_count':len(d['points'])} for d in repo.all_rows('datasets')]
def detail(id):return repo.get('datasets',id)
def create(data):return repo.put('datasets',FiducialDataset(new_id('ds'),data.name,data.source,parse_points(data.csv_text),now()))
def rename(id,data):
 d=repo.get('datasets',id);d['name']=data.name;return repo.put('datasets',d)
