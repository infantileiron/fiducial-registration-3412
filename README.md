# 皓川光学 · 标志点刚体配准

为10人光学测量组锁定毫米点对和轴系，用全量Kabsch与RANSAC稳健配准复核源到目标的proper旋转平移，逐点说明最终内点和残差。

## 真实工作场景

上游 `haochuan_fiducials_202611.csv` 为相机A与台架B的60组成对3D毫米坐标。测量组原用表格手算平移，常漏掉旋转、被错误对应拖偏、将镜像误配当作可接受变换。本系统替代点对校验、轴系口径锁定、两种拟合与工程复核；下游测量档案组读取批准的R/t与残差CSV。模拟点对不替代真实设备标定或精度保证。

六实体：FiducialDataset点对、FrameSpec轴系声明、RegistrationStudy锁定研究、RegistrationRun异步运行、AlignmentReview复核、Report报告，贯穿持久化/model/schema/service/controller/route/API/store/页面。六页为配准工作台、标志点对、轴系声明、快照与计算、变换与残差、工程复核；另有登录。工作台与结果复用RegistrationSummary、PairProjection、TransformComparison。

## 快速启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

前端 http://localhost:18234 ，API http://localhost:19234/docs ，PostgreSQL17734。Compose name=fiducial-registration，恰好frontend/backend/worker/db/redis五服务，全部健康检查与依赖健康门禁。Nginx反代/api、SPA回落；数据库/Redis/共享JSON与CSV分别使用命名卷。清理 `docker compose down -v --remove-orphans`。

| 角色 / 账号 | 页面 | 权限与典型动作 |
|---|---|---|
| admin@haochuan.test / 配准复核工程师 | 六页与审计 | 读写、批准/退回、审核最终R/t与内点 |
| analyst@haochuan.test / 光学测量分析员 | 点对、轴系、研究、结果、复核 | 导入、声明、运行、提审、生成批准报告 |
| viewer@haochuan.test / 测量档案阅览员 | 六页只读 | 查阅并下载已批准CSV |

统一演示密码 `Fiducial2026!`。PBKDF2、JWT HS256、角色依赖、actor审计、全局错误恢复与最多10个排队/运行任务。默认口令密钥仅供本地演示。

## 一天的测量剧本

1. 09:00 导入haochuan_fiducials_202611.csv，60组HC001—HC060。
2. 09:05 核查每行源xyz/目标xyz，不猜测点对、不把空值当0。
3. 09:10 声明CAMERA-A→TABLE-B、单位mm、right-handed xyz。
4. 09:15 固定阈值0.5mm、预算400次、seed2405；保存点对/轴系/参数快照与SHA256。
5. 09:20 Redis排队，独立Python worker计算全量Kabsch、最小3点RANSAC与内点精炼。
6. 09:25 在XY/XZ投影对照原始源点、目标与变换后源点；查看8个阈值外点。
7. 09:30 分开核对全点RMSE、52内点RMSE、detR=+1与精炼稳定性，分析员提审。
8. 09:40 工程师批准，阅览员下载两组R/t、原始点对、最终残差/分类与快照哈希CSV。

## 输入、轴系与快照

CSV列id,sx,sy,sz,tx,ty,tz，3—500组。ID为唯一1—30位字母数字下划线连字符；坐标有限且绝对值≤1e6毫米，全部6值完整，拒绝短行、重复ID、NaN/Inf。数据按ID稳定排序。几何共线/重合不隐式删除，在worker明确失败。

本工程只接受mm与right-handed xyz，不自动换轴、换单位。源与目标帧必须有非空且不同名称。约定列向量 y=R*x+t；CSV每行先源后目标。研究保存完整points、帧名称/单位/轴向、阈值、预算、seed、约定与源文件，规范JSON SHA256绑定。worker仅读快照；数据集后续改名不影响历史报告，既有点对/帧/研究没有修改接口。

RANSAC阈值[1e-6,100]mm、迭代1—2000、seed在[0,2147483647]；默认0.5mm/400/2405，最多10轮精炼。NumPy.float64计算，原始与结果数值以Python双精度JSON数字持久化于PostgreSQL，不在后端先做显示舍入。

## Kabsch proper SO(3)

源X、目标Y各自去质心，H=XcᵀYc=UΣVᵀ；D=diag(1,1,sign(det(VUᵀ)))，R=VDUᵀ，t=ȳ−R*x̄。由此det(R)=+1且RᵀR=I，仅旋转平移，不拟合镜像或缩放。残差||R*x_i+t−y_i||₂，RMSE=sqrt(mean(e_i²))，单位均mm。

至少3个非共线对应，源/目标中心化rank<2拒绝；rank2平面可用。rank判据使用NumPy矩阵秩的浮点SVD阈值。保存两个rank、交叉矩阵奇异值、det修正与正交误差。完整三维镜像无法由proper旋转零误差拟合，但平面镜像可能与空间旋转不可区分，不声称所有镜像均可检测。

## RANSAC、同分和精炼

每次从按ID排序的点对中固定seed抽取3点；共线样本跳过。用候选R/t对全部点计算欧氏残差，e≤阈值为内点。候选按内点数最多→内点RMSE最小→样本ID字典序比较，输入相同可复现。有限预算不保证全局最优，也不输出虚构成功概率。

最佳集合用Kabsch重拟合，再对全部点重新评估。集合一致才refinement_stable=true，最多10轮；达上限则明确警告，保留fitted_ids与最终inlier_ids，最终模型可能基于前一集合。精炼后不足3个非共线内点明确失败。返回全点残差/预测、最终分类、全点RMSE与内点RMSE；fitted_rmse单独保留拟合集合误差。不能只用内点RMSE声称全体都准确。

## 技术与开发

| 层 | 技术 |
|---|---|
| 前端 | React18 / TypeScript5.7 / Vite6 / Nginx1.28 |
| 后端 | Python3.12 / FastAPI / psycopg3 |
| 数值 | NumPy2.2.1，Kabsch SVD + 自实现固定seed RANSAC |
| 异步/数据库 | Redis7.4 / 独立worker / PostgreSQL16 |

80个代码源文件，其中src内76个职责文件。backend/src含routes/controllers/services/models/schemas/middlewares/utils/constants/config；frontend/src含api/stores/types/components/common/hooks/pages/router/utils/constants。迁移DDL在backend/migrations，advisory lock保护首次建表。自然键insert-only seed，重复不新增、不覆盖用户修改；失败记日志不阻断API。

固定种子2405：60组3D点，模拟旋转Rz(22°)Ry(−11°)、t=(12,−7,4.5)mm、坐标高斯噪声sd=.03mm，前8个目标额外偏移形成离群；算法未接收离群真值标签。默认阈值下最终52内点/8阈值外。所有真实测试/截图/报告仅在批次test-artifacts/gb-2405。

环境DATABASE_URL、REDIS_URL、JWT_SECRET、SEED_DEMO、TASK_MODE、ARTIFACT_DIR及端口/DB_PASSWORD见.env.example。本地PG/Redis配置后pip install backend/requirements.txt，运行uvicorn src.main:app --reload；前端npm ci && npm run dev，经/api反代。package/lock精确复用已测配套版本，仅改根项目名称。

枚举：backend/src/constants/enums.py(Role/RunStatus/ReviewStatus)与domain.py(单位/约定/配额)；frontend/src/constants/enums.ts(角色/状态)。共享通用组件PageTitle/Notice/StatusBadge，hooks/useResource与useSession，utils/chart与format。

边界：无自动对应、尺度拟合、镜像校正、传感器误差模型或真实设备控制。RANSAC可能漏最优集合，近共线几何数值不稳需人工核查；不作精度保证。Redis出队后强杀不自动重投，JSON载荷无多人乐观锁和迁移回滚。

## License

MIT，见LICENSE。
