import numpy as np
from src.services.geometry import point_arrays,rank_centered,evaluate
def kabsch(source,target):
 X,Y=point_arrays(source,target);rx,ry=rank_centered(X),rank_centered(Y)
 if min(rx,ry)<2:raise ValueError('至少3个非共线对应；源点或目标点中心化rank<2，无法唯一约束刚体旋转')
 cx,cy=X.mean(axis=0),Y.mean(axis=0);U,s,Vt=np.linalg.svd((X-cx).T@(Y-cy));raw=Vt.T@U.T;corrected=bool(np.linalg.det(raw)<0);D=np.eye(3);D[2,2]=-1 if corrected else 1;R=Vt.T@D@U.T;t=cy-R@cx;predicted,residuals=evaluate(X,Y,R,t)
 return {'R':R.tolist(),'t':t.tolist(),'predicted':predicted.tolist(),'residuals':residuals.tolist(),'rmse':float(np.sqrt(np.mean(residuals**2))),'max_error':float(np.max(residuals)),'det_R':float(np.linalg.det(R)),'orthogonality_error':float(np.linalg.norm(R.T@R-np.eye(3))),'source_rank':rx,'target_rank':ry,'cross_singular_values':s.tolist(),'reflection_corrected':corrected,'point_count':len(X),'note':'proper SO(3) rotation only；不拟合镜像或缩放；平面数据不能笼统识别镜像'}
