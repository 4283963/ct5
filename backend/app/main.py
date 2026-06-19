from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import upload, metrics, diagnosis

app = FastAPI(
    title="航线轨迹与燃油消耗效益分析系统",
    description="基于远洋货轮航行数据的效益分析与优化平台",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/upload", tags=["数据上传"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["指标看板"])
app.include_router(diagnosis.router, prefix="/api/diagnosis", tags=["诊断优化"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "vessel-analytics"}
