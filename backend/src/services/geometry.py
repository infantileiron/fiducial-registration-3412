import numpy as np
def point_arrays(source,target):
 try:X=np.asarray(source,dtype=np.float64);Y=np.asarray(target,dtype=np.float64)
 except (TypeError,ValueError):raise ValueError('坐标必须是有限三维数值')
 if X.ndim!=2 or X.shape[1:]!=(3,) or X.shape!=Y.shape or len(X)<3 or not np.isfinite(X).all() or not np.isfinite(Y).all():raise ValueError('需要至少3组等长有限三维点对')
 if np.max(np.abs(X))>1e6 or np.max(np.abs(Y))>1e6:raise ValueError('毫米坐标绝对值不能超过1e6')
 return X,Y
def rank_centered(X):return int(np.linalg.matrix_rank(X-X.mean(axis=0)))
def evaluate(X,Y,R,t):
 predicted=X@R.T+t;residuals=np.linalg.norm(predicted-Y,axis=1);return predicted,residuals
