# 航线轨迹与燃油消耗效益分析系统

基于远洋货轮航行数据的效益分析与优化平台，采用前后端分离架构。

## 项目架构

### 后端技术栈
- **FastAPI**: 高性能异步 Web 框架
- **Pandas**: 数据清洗与处理
- **NumPy/SciPy**: 数值计算与统计分析
- **Scikit-learn**: 异常检测（Isolation Forest）
- **Pydantic**: 数据模型验证

### 前端技术栈
- **Vue 3**: 渐进式 JavaScript 框架
- **ECharts**: 数据可视化图表库
- **Element Plus**: UI 组件库
- **Pinia**: 状态管理
- **Vue Router**: 路由管理
- **Axios**: HTTP 客户端

## 目录结构

```
ct5/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── config.py                 # 配置管理
│   │   ├── api/                      # API 路由层
│   │   │   ├── __init__.py
│   │   │   ├── upload.py             # 数据上传接口
│   │   │   ├── metrics.py            # 指标看板接口
│   │   │   └── diagnosis.py          # 诊断优化接口
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── chunk_uploader.py     # 分片上传服务
│   │   │   ├── data_processor.py     # 数据处理与清洗
│   │   │   ├── metrics_calculator.py # 效益算法计算
│   │   │   └── diagnosis_engine.py   # 诊断优化引擎
│   │   └── models/                   # 数据模型
│   │       ├── __init__.py
│   │       └── schemas.py            # Pydantic 模型
│   ├── data/                         # 数据存储目录
│   │   ├── uploads/                  # 原始上传文件
│   │   ├── chunks/                   # 上传分片临时存储
│   │   └── processed/                # 处理后的数据
│   └── requirements.txt              # Python 依赖
│
├── frontend/                         # 前端应用
│   ├── src/
│   │   ├── main.js                   # 应用入口
│   │   ├── App.vue                   # 根组件
│   │   ├── router/index.js           # 路由配置
│   │   ├── api/                      # API 调用层
│   │   │   ├── index.js              # Axios 实例
│   │   │   ├── upload.js             # 上传相关 API
│   │   │   ├── metrics.js            # 指标相关 API
│   │   │   └── diagnosis.js          # 诊断相关 API
│   │   ├── views/                    # 页面视图
│   │   │   ├── Upload.vue            # 数据上传页面
│   │   │   ├── Dashboard.vue         # 指标看板页面
│   │   │   └── Diagnosis.vue         # 诊断优化页面
│   │   ├── components/               # 可复用组件
│   │   │   └── charts/
│   │   │       ├── LineChart.vue     # 折线图组件
│   │   │       └── TrajectoryMap.vue # 轨迹图组件
│   │   ├── stores/                   # Pinia 状态管理
│   │   │   └── voyage.js             # 航次数据 store
│   │   └── utils/                    # 工具函数
│   │       ├── chunkUploader.js      # 分片上传工具
│   │       └── chartOptions.js       # 图表配置生成
│   ├── package.json                  # npm 依赖
│   ├── vite.config.js                # Vite 配置
│   └── index.html                    # HTML 模板
│
└── .gitignore
```

## 三大核心模块

### 1. 海量轨迹数据分片上传与解析模块

**功能特性：**
- 支持 GB 级大文件分片上传（默认 5MB/片）
- MD5 校验确保文件完整性
- 支持 CSV、Excel、Parquet 多种格式
- 自动识别中英文列名映射
- 数据自动清洗（去重、异常值处理）
- 自动航次识别与划分

**关键文件：**
- 后端: [chunk_uploader.py](file:///Users/kl/Documents/trae_projects2/ct5/backend/app/services/chunk_uploader.py)
- 后端: [data_processor.py](file:///Users/kl/Documents/trae_projects2/ct5/backend/app/services/data_processor.py)
- 前端: [chunkUploader.js](file:///Users/kl/Documents/trae_projects2/ct5/frontend/src/utils/chunkUploader.js)
- 前端: [Upload.vue](file:///Users/kl/Documents/trae_projects2/ct5/frontend/src/views/Upload.vue)

### 2. 航线多维指标对比看板

**功能特性：**
- 多航次航速、油耗、风速、效率对比
- 航线轨迹可视化展示
- 航速-油耗相关性分析
- 滚动燃油效率趋势分析
- 最优航速区间识别
- 风向影响量化评估

**关键文件：**
- 后端: [metrics_calculator.py](file:///Users/kl/Documents/trae_projects2/ct5/backend/app/services/metrics_calculator.py)
- 后端: [metrics.py](file:///Users/kl/Documents/trae_projects2/ct5/backend/app/api/metrics.py)
- 前端: [Dashboard.vue](file:///Users/kl/Documents/trae_projects2/ct5/frontend/src/views/Dashboard.vue)
- 前端: [chartOptions.js](file:///Users/kl/Documents/trae_projects2/ct5/frontend/src/utils/chartOptions.js)

### 3. 低效航线诊断优化模块

**功能特性：**
- 基于 Isolation Forest 的异常检测
- 航速偏离最优区间识别
- 燃油效率低下诊断
- 风阻影响量化评估
- 多维度问题分级（高/中/低）
- 个性化优化建议方案
- 投资回收期估算

**关键文件：**
- 后端: [diagnosis_engine.py](file:///Users/kl/Documents/trae_projects2/ct5/backend/app/services/diagnosis_engine.py)
- 后端: [diagnosis.py](file:///Users/kl/Documents/trae_projects2/ct5/backend/app/api/diagnosis.py)
- 前端: [Diagnosis.vue](file:///Users/kl/Documents/trae_projects2/ct5/frontend/src/views/Diagnosis.vue)

## 快速开始

### 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（可选）
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档地址: http://localhost:8000/docs

### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问地址: http://localhost:5173

## 数据格式要求

### 必填字段

| 字段名 | 说明 | 范围 |
|--------|------|------|
| timestamp | 时间戳 | ISO 格式 |
| longitude | 经度 | -180 ~ 180 |
| latitude | 纬度 | -90 ~ 90 |
| speed | 航速 | 0 ~ 40 节 |
| fuel_consumption | 油耗 | >= 0 吨/小时 |
| wind_speed | 风速 | >= 0 m/s |
| wind_direction | 风向 | 0 ~ 360 度 |
| course | 航向 | 0 ~ 360 度 |

### 可选字段

| 字段名 | 说明 |
|--------|------|
| vessel_name | 船名 |
| voyage_id | 航次ID |
| departure_port | 出发港 |
| arrival_port | 到达港 |
| engine_power | 主机功率 |
| draft | 吃水深度 |

## 核心算法说明

### 1. 燃油效率计算
```
燃油效率 = 航行距离 / 燃油消耗量 × 1000 (kg/海里)
```

### 2. 航速-油耗相关性
采用 Pearson 相关系数分析航速与油耗的线性关系，结合二次多项式拟合建立油耗预测模型。

### 3. 异常检测
使用 Isolation Forest 算法识别异常数据点，contamination 设置为 2%。

### 4. 效益评分模型
综合考虑航速偏离、油耗异常、风阻影响等多维度因素，加权计算综合效益得分（0-100分）。

## 开发规范

- 代码按领域职责划分多文件，避免长文件
- 后端使用类型提示 (Type Hints)
- 前端使用 Vue 3 Composition API
- API 遵循 RESTful 设计规范
- 错误处理统一化，返回结构化错误信息

## License

MIT
