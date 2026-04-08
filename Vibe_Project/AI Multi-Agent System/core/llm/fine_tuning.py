"""
微调接口模块 - Fine-tuning API
=============================

【功能】
1. 微调任务管理 - 创建、查看、取消微调任务
2. 微调模型使用 - 使用微调后的模型进行推理
3. 训练数据管理 - 上传、管理训练数据
4. 模型版本控制 - 管理多个模型版本

【支持的Provider】
- OpenAI GPT微调
- Anthropic Claude微调（如果有API）
"""

from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import os
import json
import time


class FineTuningStatus(Enum):
    """微调状态"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    SUCCEEDED = "succeeded"  # 成功
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class ModelVersion(Enum):
    """模型版本"""
    BASE = "base"           # 基础模型
    FINE_TUNED = "fine_tuned"  # 微调后的模型


@dataclass
class TrainingData:
    """训练数据"""
    id: str
    file_name: str
    file_size: int
    status: str  # uploaded, processed, error
    record_count: int
    created_at: datetime


@dataclass
class FineTuningJob:
    """微调任务"""
    id: str
    model: str  # 基础模型
    fine_tuned_model: Optional[str] = None  # 微调后的模型
    status: FineTuningStatus = FineTuningStatus.PENDING
    training_file_id: Optional[str] = None
    validation_file_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    error: Optional[str] = None

    # 训练参数
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 1e-5

    # 结果指标
    training_loss: Optional[float] = None
    validation_loss: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "model": self.model,
            "fine_tuned_model": self.fine_tuned_model,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "error": self.error,
            "training_loss": self.training_loss,
            "validation_loss": self.validation_loss
        }


@dataclass
class FineTunedModel:
    """微调后的模型"""
    model_name: str
    base_model: str
    job_id: str
    created_at: datetime
    description: str = ""
    metrics: Dict[str, float] = field(default_factory=dict)


class FineTuningManager:
    """微调管理器

    【功能】
    - 创建微调任务
    - 追踪微调状态
    - 管理微调后的模型
    - 使用微调模型进行推理
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = "openai"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.provider = provider.lower()

        # 微调任务存储（内存中，生产环境应使用数据库）
        self.jobs: Dict[str, FineTuningJob] = {}
        self.models: Dict[str, FineTunedModel] = {}

        # OpenAI客户端
        self._openai_client = None

    def _get_openai_client(self):
        """获取OpenAI客户端"""
        if self._openai_client is None:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("请安装openai: pip install openai")
        return self._openai_client

    def create_training_data(
        self,
        file_path: str,
        description: str = ""
    ) -> TrainingData:
        """创建训练数据

        Args:
            file_path: 训练数据文件路径（JSONL格式）
            description: 数据描述

        Returns:
            TrainingData: 训练数据信息
        """
        import hashlib

        # 生成ID
        file_id = hashlib.md5(f"{file_path}{time.time()}".encode()).hexdigest()[:8]

        # 获取文件大小
        file_size = os.path.getsize(file_path)

        # 计算记录数
        record_count = 0
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record_count += 1

        return TrainingData(
            id=file_id,
            file_name=os.path.basename(file_path),
            file_size=file_size,
            status="uploaded",
            record_count=record_count,
            created_at=datetime.now()
        )

    def prepare_training_data(
        self,
        conversations: List[Dict[str, str]],
        output_file: str
    ) -> TrainingData:
        """准备训练数据

        Args:
            conversations: 对话列表 [{"messages": [{"role": "user", "content": "..."}]}]
            output_file: 输出文件路径

        Returns:
            TrainingData: 训练数据信息
        """
        # 写入JSONL文件
        with open(output_file, 'w', encoding='utf-8') as f:
            for conv in conversations:
                f.write(json.dumps(conv, ensure_ascii=False) + '\n')

        return self.create_training_data(output_file)

    def create_fine_tuning_job(
        self,
        training_file_path: str,
        base_model: str = "gpt-3.5-turbo",
        validation_file_path: Optional[str] = None,
        epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 1e-5,
        description: str = "",
        **kwargs
    ) -> FineTuningJob:
        """创建微调任务

        Args:
            training_file_path: 训练数据文件路径
            base_model: 基础模型
            validation_file_path: 验证数据文件路径（可选）
            epochs: 训练轮数
            batch_size: 批次大小
            learning_rate: 学习率
            description: 任务描述

        Returns:
            FineTuningJob: 微调任务信息
        """
        import hashlib

        # 生成任务ID
        job_id = f"ft-{hashlib.md5(f'{training_file_path}{time.time()}'.encode()).hexdigest()[:8]}"

        # 创建训练数据
        training_data = self.create_training_data(training_file_path)

        # 创建微调任务
        job = FineTuningJob(
            id=job_id,
            model=base_model,
            status=FineTuningStatus.PENDING,
            training_file_id=training_data.id,
            epochs=epochs,
            batch_size=batch_size,
            learning_rate=learning_rate
        )

        # 保存到内存
        self.jobs[job_id] = job

        # 如果是OpenAI，使用API创建
        if self.provider == "openai":
            self._create_openai_fine_tuning(job, training_file_path, validation_file_path, **kwargs)

        return job

    def _create_openai_fine_tuning(
        self,
        job: FineTuningJob,
        training_file_path: str,
        validation_file_path: Optional[str],
        **kwargs
    ):
        """使用OpenAI API创建微调任务"""
        client = self._get_openai_client()

        try:
            # 上传训练文件
            with open(training_file_path, 'rb') as f:
                training_file = client.files.create(
                    file=f,
                    purpose="fine-tune"
                )

            # 构建参数
            create_params = {
                "training_file": training_file.id,
                "model": job.model,
                "hyperparameters": {
                    "n_epochs": job.epochs,
                    "batch_size": job.batch_size,
                    "learning_rate_multiplier": job.learning_rate / 1e-5  # 转换
                }
            }

            # 添加验证文件
            if validation_file_path:
                with open(validation_file_path, 'rb') as f:
                    validation_file = client.files.create(
                        file=f,
                        purpose="fine-tune"
                    )
                    create_params["validation_file"] = validation_file.id

            # 创建微调任务
            ft_job = client.fine_tuning.jobs.create(**create_params)

            # 更新任务信息
            job.id = ft_job.id
            self.jobs[job.id] = job

        except Exception as e:
            job.status = FineTuningStatus.FAILED
            job.error = str(e)

    def get_fine_tuning_job(self, job_id: str) -> Optional[FineTuningJob]:
        """获取微调任务信息"""
        if job_id in self.jobs:
            job = self.jobs[job_id]

            # 如果是OpenAI，同步最新状态
            if self.provider == "openai":
                self._sync_openai_job_status(job)

            return job

        return None

    def _sync_openai_job_status(self, job: FineTuningJob):
        """同步OpenAI微调任务状态"""
        if job.status in [FineTuningStatus.SUCCEEDED, FineTuningStatus.FAILED, FineTuningStatus.CANCELLED]:
            return  # 已完成，不再同步

        client = self._get_openai_client()

        try:
            ft_job = client.fine_tuning.jobs.retrieve(job.id)

            # 更新状态
            status_map = {
                "pending": FineTuningStatus.PENDING,
                "running": FineTuningStatus.RUNNING,
                "succeeded": FineTuningStatus.SUCCEEDED,
                "failed": FineTuningStatus.FAILED,
                "cancelled": FineTuningStatus.CANCELLED
            }
            job.status = status_map.get(ft_job.status, FineTuningStatus.PENDING)

            # 更新微调后的模型
            if ft_job.fine_tuned_model:
                job.fine_tuned_model = ft_job.fine_tuned_model

            # 获取训练结果
            if job.status == FineTuningStatus.SUCCEEDED:
                job.finished_at = datetime.now()

                # 获取最终指标
                try:
                    events = client.fine_tuning.jobs.list_events(job.id, limit=10)
                    for event in events.data:
                        if event.data.get("train_loss"):
                            job.training_loss = event.data["train_loss"]
                except:
                    pass

        except Exception as e:
            job.error = str(e)

    def list_fine_tuning_jobs(self) -> List[FineTuningJob]:
        """列出所有微调任务"""
        # 同步状态
        for job in self.jobs.values():
            if job.status not in [FineTuningStatus.SUCCEEDED, FineTuningStatus.FAILED, FineTuningStatus.CANCELLED]:
                if self.provider == "openai":
                    self._sync_openai_job_status(job)

        return list(self.jobs.values())

    def cancel_fine_tuning_job(self, job_id: str) -> bool:
        """取消微调任务"""
        job = self.get_fine_tuning_job(job_id)
        if not job:
            return False

        if job.status in [FineTuningStatus.SUCCEEDED, FineTuningStatus.FAILED]:
            return False  # 已结束的任务无法取消

        if self.provider == "openai":
            client = self._get_openai_client()
            try:
                client.fine_tuning.jobs.cancel(job.id)
                job.status = FineTuningStatus.CANCELLED
                return True
            except Exception as e:
                job.error = str(e)
                return False

        return False

    def use_fine_tuned_model(
        self,
        job_id: str,
        callback: Optional[Callable] = None
    ) -> Optional[str]:
        """获取微调模型的名称，用于推理

        Args:
            job_id: 微调任务ID
            callback: 如果模型未就绪，传入回调函数

        Returns:
            微调后的模型名称，如果未就绪返回None
        """
        job = self.get_fine_tuning_job(job_id)

        if not job:
            return None

        if job.status != FineTuningStatus.SUCCEEDED:
            if callback:
                callback(job)
            return None

        return job.fine_tuned_model

    def register_fine_tuned_model(
        self,
        model_name: str,
        job_id: str,
        base_model: str,
        description: str = "",
        metrics: Optional[Dict[str, float]] = None
    ):
        """注册微调后的模型

        【使用场景】
        - 手动管理模型
        - 不通过微调流程，直接使用已有模型
        """
        self.models[model_name] = FineTunedModel(
            model_name=model_name,
            base_model=base_model,
            job_id=job_id,
            created_at=datetime.now(),
            description=description,
            metrics=metrics or {}
        )

    def get_fine_tuned_model(self, model_name: str) -> Optional[FineTunedModel]:
        """获取微调模型信息"""
        return self.models.get(model_name)

    def list_fine_tuned_models(self) -> List[FineTunedModel]:
        """列出所有微调模型"""
        return list(self.models.values())


class FineTuningWrapper:
    """微调模型包装器

    【功能】
    - 使用微调后的模型进行推理
    - 自动切换基础模型和微调模型
    - 统一接口
    """

    def __init__(
        self,
        base_llm: Any,
        fine_tuning_manager: FineTuningManager
    ):
        self.base_llm = base_llm
        self.ft_manager = fine_tuning_manager

        # 当前使用的模型
        self.current_model_name: Optional[str] = None
        self.is_fine_tuned = False

    def use_fine_tuned(self, job_id: str) -> bool:
        """切换到微调模型

        Returns:
            是否切换成功
        """
        model_name = self.ft_manager.use_fine_tuned_model(job_id)

        if model_name:
            self.current_model_name = model_name
            self.is_fine_tuned = True
            return True

        return False

    def use_base_model(self):
        """切换回基础模型"""
        self.current_model_name = None
        self.is_fine_tuned = False

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Any:
        """生成响应"""
        if self.is_fine_tuned:
            # 使用微调模型
            kwargs["model"] = self.current_model_name
            return await self.base_llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )
        else:
            # 使用基础模型
            return await self.base_llm.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                **kwargs
            )


# 全局实例
_fine_tuning_manager: Optional[FineTuningManager] = None


def get_fine_tuning_manager() -> FineTuningManager:
    """获取微调管理器实例"""
    global _fine_tuning_manager
    if _fine_tuning_manager is None:
        _fine_tuning_manager = FineTuningManager()
    return _fine_tuning_manager


# ========== 使用示例 ==========
"""
【完整使用流程】

# 1. 创建微调管理器
ft_manager = get_fine_tuning_manager()

# 2. 准备训练数据
conversations = [
    {
        "messages": [
            {"role": "system", "content": "你是一个代码审查助手"},
            {"role": "user", "content": "帮我审查这段代码"},
            {"role": "assistant", "content": "好的，请提供代码"}
        ]
    }
]

# 保存为JSONL
ft_manager.prepare_training_data(conversations, "training_data.jsonl")

# 3. 创建微调任务
job = ft_manager.create_fine_tuning_job(
    training_file_path="training_data.jsonl",
    base_model="gpt-3.5-turbo",
    epochs=3,
    description="代码审查助手"
)

print(f"微调任务ID: {job.id}")

# 4. 追踪微调状态
while True:
    job = ft_manager.get_fine_tuning_job(job.id)
    print(f"状态: {job.status.value}")

    if job.status == FineTuningStatus.SUCCEEDED:
        print(f"微调后的模型: {job.fine_tuned_model}")
        break
    elif job.status == FineTuningStatus.FAILED:
        print(f"失败原因: {job.error}")
        break

    time.sleep(60)  # 每分钟检查一次

# 5. 使用微调模型
wrapper = FineTuningWrapper(base_llm, ft_manager)
wrapper.use_fine_tuned(job.id)

response = await wrapper.generate("帮我审查这段代码")
"""


class FineTuningAPI:
    """微调API（用于外部调用）"""

    def __init__(self):
        self.manager = get_fine_tuning_manager()

    def create_job(
        self,
        training_file: str,
        base_model: str = "gpt-3.5-turbo",
        **kwargs
    ) -> Dict:
        """创建微调任务"""
        job = self.manager.create_fine_tuning_job(
            training_file_path=training_file,
            base_model=base_model,
            **kwargs
        )
        return job.to_dict()

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """获取任务状态"""
        job = self.manager.get_fine_tuning_job(job_id)
        return job.to_dict() if job else None

    def list_jobs(self) -> List[Dict]:
        """列出所有任务"""
        return [job.to_dict() for job in self.manager.list_fine_tuning_jobs()]

    def cancel_job(self, job_id: str) -> bool:
        """取消任务"""
        return self.manager.cancel_fine_tuning_job(job_id)
