import numpy as np
from src.services.kabsch import kabsch
from src.services.ransac import ransac
def analyze(snapshot,checksum):
 points=snapshot['points'];X=[p['source'] for p in points];Y=[p['target'] for p in points];ids=[p['id'] for p in points];full=kabsch(X,Y);robust=ransac(X,Y,ids,snapshot['threshold_mm'],snapshot['iterations'],snapshot['seed']);rows=[]
 for i,p in enumerate(points):rows.append({**p,'full_predicted':full['predicted'][i],'robust_predicted':robust['predicted'][i],'full_residual':full['residuals'][i],'robust_residual':robust['residuals'][i],'inlier':robust['inlier_mask'][i]})
 return {'rows':rows,'point_count':len(points),'full':full,'robust':robust,'frame':snapshot['frame'],'threshold_mm':snapshot['threshold_mm'],'iterations':snapshot['iterations'],'seed':snapshot['seed'],'source':snapshot['source'],'convention':snapshot['convention'],'checksum':checksum,'limitations':['y=R*x+t，全部欧氏残差为毫米；proper rotation，不拟合缩放或镜像','RANSAC有限预算不保证全局最优；最终内点由精炼后的模型重新评估','平面rank2可用，但平面镜像可能与空间旋转不可区分','模拟光学点对，不替代真实设备标定或精度保证']}
