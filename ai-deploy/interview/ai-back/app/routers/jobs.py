from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.job import Job

router = APIRouter()


# 接口：获取所有岗位列表
@router.get("/api/jobs")
def get_all_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()
    return [
        {
            "id": job.id,
            "title": job.title,
            "category": job.category,
            "desc": job.desc,
            "icon": job.icon,
            "bgColor": job.bgColor
        } for job in jobs
    ]


# 接口：一键灌入初始岗位数据
@router.post("/api/jobs/init")
def init_default_jobs(db: Session = Depends(get_db)):
    if db.query(Job).first():
        return {"message": "数据已存在，无需重复初始化"}

    initial_jobs = [
        Job(title='Java后端', category='后端开发', desc='深入并发编程、JVM调优与Spring微服务架构实战。', icon='☕',
            bgColor='#E0F2FE', job_key='java'),
        Job(title='Web前端', category='前端开发', desc='夯实JS基础，掌握Vue/React现代框架与性能优化。', icon='⚡',
            bgColor='#FEF3C7', job_key='front'),
        Job(title='Python算法', category='人工智能', desc='聚焦数据结构、机器学习模型与底层逻辑推导。', icon='🐍',
            bgColor='#DCFCE7', job_key='python'),
        Job(title='C++研发', category='后端开发', desc='底层系统开发、高性能计算与音视频处理。', icon='⚙️',
            bgColor='#F3E8FF', job_key='c++'),
        Job(title='测试开发工程师', category='质量保障', desc='自动化测试框架搭建与持续集成流水线建设。', icon='🐛',
            bgColor='#FCE7F3', job_key='test'),
        Job(title='数据分析师', category='数据', desc='基于海量数据进行清洗、挖掘与商业可视化分析。', icon='📊',
            bgColor='#E0E7FF', job_key='data'),
        Job(title='Go语言开发', category='后端开发', desc='掌握高并发网络编程与云原生微服务架构。', icon='🐹',
            bgColor='#CCFBF1', job_key='go'),
        Job(title='Android开发', category='移动端', desc='精通移动端性能优化、UI绘制原理与架构设计。', icon='📱',
            bgColor='#D1FAE5', job_key='android'),
        Job(title='iOS开发', category='移动端', desc='深入Objective-C/Swift与苹果生态底层机制。', icon='🍎',
            bgColor='#F3F4F6', job_key='ios'),
        Job(title='运维工程师', category='技术支持', desc='保障千万级并发系统稳定，精通K8s与自动化部署。', icon='🛠️',
            bgColor='#FFF7ED', job_key='general1')
    ]
    db.add_all(initial_jobs)
    db.commit()
    return {"message": "10个初始岗位数据已成功灌入数据库！"}
