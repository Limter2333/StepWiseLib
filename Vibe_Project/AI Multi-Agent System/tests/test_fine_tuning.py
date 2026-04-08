"""
微调模块测试
============

【功能】
- 微调任务管理测试
- 训练数据管理测试
- 微调模型注册测试
- 状态管理测试
"""

import sys
import os
import tempfile
import importlib.util
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_module(module_name, file_path):
    """直接加载模块，避免循环依赖"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_fine_tuning_status_enum():
    """测试微调状态枚举"""
    fine_tuning = load_module('fine_tuning', 'core/llm/fine_tuning.py')
    FineTuningStatus = fine_tuning.FineTuningStatus

    assert FineTuningStatus.PENDING.value == "pending"
    assert FineTuningStatus.RUNNING.value == "running"
    assert FineTuningStatus.SUCCEEDED.value == "succeeded"
    assert FineTuningStatus.FAILED.value == "failed"
    assert FineTuningStatus.CANCELLED.value == "cancelled"

    print("    - FineTuningStatus enum OK")


def test_model_version_enum():
    """测试模型版本枚举"""
    fine_tuning = load_module('fine_tuning2', 'core/llm/fine_tuning.py')
    ModelVersion = fine_tuning.ModelVersion

    assert ModelVersion.BASE.value == "base"
    assert ModelVersion.FINE_TUNED.value == "fine_tuned"

    print("    - ModelVersion enum OK")


def test_training_data_creation():
    """测试训练数据创建"""
    fine_tuning = load_module('fine_tuning3', 'core/llm/fine_tuning.py')
    TrainingData = fine_tuning.TrainingData
    from datetime import datetime

    data = TrainingData(
        id="test-001",
        file_name="train.jsonl",
        file_size=1024,
        status="uploaded",
        record_count=100,
        created_at=datetime.now()
    )

    assert data.id == "test-001"
    assert data.file_name == "train.jsonl"
    assert data.file_size == 1024
    assert data.status == "uploaded"
    assert data.record_count == 100

    print("    - TrainingData creation OK")


def test_fine_tuning_job_creation():
    """测试微调任务创建"""
    fine_tuning = load_module('fine_tuning4', 'core/llm/fine_tuning.py')
    FineTuningJob = fine_tuning.FineTuningJob
    FineTuningStatus = fine_tuning.FineTuningStatus
    from datetime import datetime

    job = FineTuningJob(
        id="ft-001",
        model="gpt-3.5-turbo",
        status=FineTuningStatus.PENDING,
        epochs=3,
        batch_size=4,
        learning_rate=1e-5
    )

    assert job.id == "ft-001"
    assert job.model == "gpt-3.5-turbo"
    assert job.status == FineTuningStatus.PENDING
    assert job.epochs == 3
    assert job.batch_size == 4
    assert job.learning_rate == 1e-5

    print("    - FineTuningJob creation OK")


def test_fine_tuning_job_to_dict():
    """测试微调任务转字典"""
    fine_tuning = load_module('fine_tuning5', 'core/llm/fine_tuning.py')
    FineTuningJob = fine_tuning.FineTuningJob
    FineTuningStatus = fine_tuning.FineTuningStatus

    job = FineTuningJob(
        id="ft-001",
        model="gpt-3.5-turbo",
        status=FineTuningStatus.SUCCEEDED,
        fine_tuned_model="ft:gpt-3.5-turbo:my-model"
    )

    d = job.to_dict()

    assert d["id"] == "ft-001"
    assert d["model"] == "gpt-3.5-turbo"
    assert d["status"] == "succeeded"
    assert d["fine_tuned_model"] == "ft:gpt-3.5-turbo:my-model"
    assert "created_at" in d

    print("    - FineTuningJob to_dict OK")


def test_fine_tuned_model_creation():
    """测试微调模型创建"""
    fine_tuning = load_module('fine_tuning6', 'core/llm/fine_tuning.py')
    FineTunedModel = fine_tuning.FineTunedModel
    from datetime import datetime

    model = FineTunedModel(
        model_name="my-fine-tuned-model",
        base_model="gpt-3.5-turbo",
        job_id="ft-001",
        created_at=datetime.now(),
        description="Test model",
        metrics={"accuracy": 0.95}
    )

    assert model.model_name == "my-fine-tuned-model"
    assert model.base_model == "gpt-3.5-turbo"
    assert model.metrics["accuracy"] == 0.95

    print("    - FineTunedModel creation OK")


def test_fine_tuning_manager_init():
    """测试微调管理器初始化"""
    fine_tuning = load_module('fine_tuning7', 'core/llm/fine_tuning.py')
    FineTuningManager = fine_tuning.FineTuningManager

    # 不带API key初始化
    manager = FineTuningManager(provider="openai")

    assert manager.provider == "openai"
    assert manager.jobs == {}
    assert manager.models == {}

    print("    - FineTuningManager init OK")


def test_prepare_training_data():
    """测试准备训练数据"""
    fine_tuning = load_module('fine_tuning8', 'core/llm/fine_tuning.py')
    FineTuningManager = fine_tuning.FineTuningManager

    manager = FineTuningManager(provider="openai")

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
        f.write('{"messages": [{"role": "user", "content": "Hello"}]}\n')
        f.write('{"messages": [{"role": "user", "content": "World"}]}\n')
        temp_path = f.name

    try:
        conversations = [
            {"messages": [{"role": "user", "content": "Hello"}]},
            {"messages": [{"role": "user", "content": "World"}]}
        ]
        output_file = tempfile.mktemp(suffix='.jsonl')

        try:
            result = manager.prepare_training_data(conversations, output_file)

            assert result.record_count == 2
            assert result.status == "uploaded"
            assert os.path.exists(output_file)

            print("    - Prepare training data OK")
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    finally:
        os.unlink(temp_path)


def test_create_training_data():
    """测试创建训练数据"""
    fine_tuning = load_module('fine_tuning9', 'core/llm/fine_tuning.py')
    FineTuningManager = fine_tuning.FineTuningManager

    manager = FineTuningManager(provider="openai")

    # 创建临时JSONL文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
        f.write('{"messages": [{"role": "user", "content": "Test"}]}\n')
        f.write('{"messages": [{"role": "user", "content": "Data"}]}\n')
        temp_path = f.name

    try:
        result = manager.create_training_data(temp_path)

        assert result.record_count == 2
        assert result.status == "uploaded"
        assert result.file_name.endswith(".jsonl")

        print("    - Create training data OK")
    finally:
        os.unlink(temp_path)


def test_register_fine_tuned_model():
    """测试注册微调模型"""
    fine_tuning = load_module('fine_tuning10', 'core/llm/fine_tuning.py')
    FineTuningManager = fine_tuning.FineTuningManager

    manager = FineTuningManager(provider="openai")

    manager.register_fine_tuned_model(
        model_name="my-model-v1",
        job_id="ft-001",
        base_model="gpt-3.5-turbo",
        description="Test model v1",
        metrics={"accuracy": 0.95}
    )

    model = manager.get_fine_tuned_model("my-model-v1")

    assert model is not None
    assert model.model_name == "my-model-v1"
    assert model.base_model == "gpt-3.5-turbo"
    assert model.metrics["accuracy"] == 0.95

    print("    - Register fine-tuned model OK")


def test_list_fine_tuned_models():
    """测试列出微调模型"""
    fine_tuning = load_module('fine_tuning11', 'core/llm/fine_tuning.py')
    FineTuningManager = fine_tuning.FineTuningManager

    manager = FineTuningManager(provider="openai")

    # 注册多个模型
    manager.register_fine_tuned_model("model-1", "ft-1", "gpt-3.5-turbo")
    manager.register_fine_tuned_model("model-2", "ft-2", "gpt-4")

    models = manager.list_fine_tuned_models()

    assert len(models) == 2

    print("    - List fine-tuned models OK")


def test_fine_tuning_wrapper():
    """测试微调包装器"""
    fine_tuning = load_module('fine_tuning12', 'core/llm/fine_tuning.py')
    FineTuningWrapper = fine_tuning.FineTuningWrapper
    FineTuningManager = fine_tuning.FineTuningManager

    # 创建模拟的base_llm
    class MockLLM:
        async def generate(self, prompt, **kwargs):
            return f"Response to: {prompt}"

    manager = FineTuningManager(provider="openai")
    wrapper = FineTuningWrapper(base_llm=MockLLM(), fine_tuning_manager=manager)

    # 默认使用基础模型
    assert wrapper.is_fine_tuned == False
    assert wrapper.current_model_name is None

    # 切换回基础模型
    wrapper.use_base_model()
    assert wrapper.is_fine_tuned == False

    print("    - FineTuningWrapper OK")


def test_fine_tuning_api():
    """测试微调API"""
    fine_tuning = load_module('fine_tuning13', 'core/llm/fine_tuning.py')
    FineTuningAPI = fine_tuning.FineTuningAPI

    api = FineTuningAPI()

    assert api.manager is not None

    print("    - FineTuningAPI OK")


class TestFineTuningEdgeCases:
    """Fine-tuning模块边界情况测试"""

    def test_training_data_with_empty_file(self):
        """测试空文件创建训练数据"""
        fine_tuning = load_module('ft_edge_1', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager

        manager = FineTuningManager(provider="openai")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as f:
            f.write('\n\n\n')  # 空行
            temp_path = f.name

        try:
            result = manager.create_training_data(temp_path)
            assert result.record_count == 0
            assert result.status == "uploaded"
            print("    - Empty file training data OK")
        finally:
            os.unlink(temp_path)

    def test_prepare_training_data_with_empty_conversations(self):
        """测试空对话列表准备训练数据"""
        fine_tuning = load_module('ft_edge_2', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager

        manager = FineTuningManager(provider="openai")
        output_file = tempfile.mktemp(suffix='.jsonl')

        try:
            result = manager.prepare_training_data([], output_file)
            assert result.record_count == 0
            assert os.path.exists(output_file)
            print("    - Empty conversations OK")
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_prepare_training_data_with_malformed_json(self):
        """测试格式化错误的JSON数据"""
        fine_tuning = load_module('ft_edge_3', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager

        manager = FineTuningManager(provider="openai")
        output_file = tempfile.mktemp(suffix='.jsonl')

        try:
            conversations = [
                {"messages": [{"role": "user", "content": "Hello"}]},
                "not a dict",  # 错误格式
                {"messages": [{"role": "assistant", "content": "World"}]}
            ]
            result = manager.prepare_training_data(conversations, output_file)
            # 写入时错误格式会被json.dumps转为字符串
            assert result.record_count == 3
            print("    - Malformed JSON handling OK")
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_get_nonexistent_fine_tuning_job(self):
        """测试获取不存在的微调任务"""
        fine_tuning = load_module('ft_edge_4', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager

        manager = FineTuningManager(provider="openai")
        result = manager.get_fine_tuning_job("nonexistent-job-id")
        assert result is None
        print("    - Nonexistent job OK")

    def test_get_nonexistent_fine_tuned_model(self):
        """测试获取不存在的微调模型"""
        fine_tuning = load_module('ft_edge_5', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager

        manager = FineTuningManager(provider="openai")
        result = manager.get_fine_tuned_model("nonexistent-model")
        assert result is None
        print("    - Nonexistent model OK")

    def test_cancel_nonexistent_job(self):
        """测试取消不存在的任务"""
        fine_tuning = load_module('ft_edge_6', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager

        manager = FineTuningManager(provider="openai")
        result = manager.cancel_fine_tuning_job("nonexistent-job-id")
        assert result is False
        print("    - Cancel nonexistent job OK")

    def test_cancel_completed_job(self):
        """测试取消已完成的任务（应该失败）"""
        fine_tuning = load_module('ft_edge_7', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager
        FineTuningStatus = fine_tuning.FineTuningStatus

        manager = FineTuningManager(provider="openai")

        # 手动创建一个已完成的job
        job = fine_tuning.FineTuningJob(
            id="completed-job",
            model="gpt-3.5-turbo",
            status=FineTuningStatus.SUCCEEDED
        )
        manager.jobs["completed-job"] = job

        result = manager.cancel_fine_tuning_job("completed-job")
        assert result is False
        print("    - Cancel completed job OK")

    def test_use_fine_tuned_model_pending_job(self):
        """测试微调模型未就绪时使用"""
        fine_tuning = load_module('ft_edge_8', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager
        FineTuningStatus = fine_tuning.FineTuningStatus

        # 使用非openai provider避免API调用
        manager = FineTuningManager(provider="anthropic")

        # 创建pending状态的job
        job = fine_tuning.FineTuningJob(
            id="pending-job",
            model="gpt-3.5-turbo",
            status=FineTuningStatus.PENDING
        )
        manager.jobs["pending-job"] = job

        result = manager.use_fine_tuned_model("pending-job")
        assert result is None
        print("    - Use fine-tuned model on pending job OK")

    def test_use_fine_tuned_model_failed_job(self):
        """测试微调失败的任务"""
        fine_tuning = load_module('ft_edge_9', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager
        FineTuningStatus = fine_tuning.FineTuningStatus

        manager = FineTuningManager(provider="openai")

        job = fine_tuning.FineTuningJob(
            id="failed-job",
            model="gpt-3.5-turbo",
            status=FineTuningStatus.FAILED
        )
        manager.jobs["failed-job"] = job

        result = manager.use_fine_tuned_model("failed-job")
        assert result is None
        print("    - Use fine-tuned model on failed job OK")

    def test_fine_tuning_wrapper_use_nonexistent_job(self):
        """测试wrapper使用不存在的job"""
        fine_tuning = load_module('ft_edge_10', 'core/llm/fine_tuning.py')
        FineTuningWrapper = fine_tuning.FineTuningWrapper
        FineTuningManager = fine_tuning.FineTuningManager

        class MockLLM:
            async def generate(self, prompt, **kwargs):
                return f"Response to: {prompt}"

        manager = FineTuningManager(provider="openai")
        wrapper = FineTuningWrapper(base_llm=MockLLM(), fine_tuning_manager=manager)

        result = wrapper.use_fine_tuned("nonexistent-job")
        assert result is False
        assert wrapper.is_fine_tuned is False
        print("    - Wrapper with nonexistent job OK")

    def test_fine_tuning_wrapper_generate_base_model(self):
        """测试wrapper使用基础模型生成"""
        fine_tuning = load_module('ft_edge_11', 'core/llm/fine_tuning.py')
        FineTuningWrapper = fine_tuning.FineTuningWrapper
        FineTuningManager = fine_tuning.FineTuningManager

        class MockLLM:
            async def generate(self, prompt, **kwargs):
                return f"Mock response to: {prompt}"

        manager = FineTuningManager(provider="openai")
        wrapper = FineTuningWrapper(base_llm=MockLLM(), fine_tuning_manager=manager)

        wrapper.use_base_model()
        assert wrapper.is_fine_tuned is False

        import asyncio
        result = asyncio.run(wrapper.generate("test prompt"))
        assert "Mock response" in result
        print("    - Wrapper base model generate OK")

    def test_fine_tuning_api_get_nonexistent_job(self):
        """测试API获取不存在的job"""
        fine_tuning = load_module('ft_edge_12', 'core/llm/fine_tuning.py')
        FineTuningAPI = fine_tuning.FineTuningAPI

        api = FineTuningAPI()
        result = api.get_job_status("nonexistent-job")
        assert result is None
        print("    - API get nonexistent job OK")

    def test_fine_tuning_api_cancel_nonexistent_job(self):
        """测试API取消不存在的job"""
        fine_tuning = load_module('ft_edge_13', 'core/llm/fine_tuning.py')
        FineTuningAPI = fine_tuning.FineTuningAPI

        api = FineTuningAPI()
        result = api.cancel_job("nonexistent-job")
        assert result is False
        print("    - API cancel nonexistent job OK")

    def test_fine_tuning_job_to_dict_with_none_fields(self):
        """测试to_dict处理None字段"""
        fine_tuning = load_module('ft_edge_14', 'core/llm/fine_tuning.py')
        FineTuningJob = fine_tuning.FineTuningJob
        FineTuningStatus = fine_tuning.FineTuningStatus

        job = FineTuningJob(
            id="test-job",
            model="gpt-3.5-turbo",
            status=FineTuningStatus.PENDING
            # 不设置可选字段
        )

        d = job.to_dict()
        assert d["id"] == "test-job"
        assert d["fine_tuned_model"] is None
        assert d["error"] is None
        assert d["training_loss"] is None
        assert d["validation_loss"] is None
        assert d["finished_at"] is None
        print("    - to_dict with None fields OK")

    def test_fine_tuning_manager_multiple_models(self):
        """测试管理器注册多个模型"""
        fine_tuning = load_module('ft_edge_15', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager

        manager = FineTuningManager(provider="openai")

        manager.register_fine_tuned_model("model-1", "ft-1", "gpt-3.5-turbo", metrics={"acc": 0.9})
        manager.register_fine_tuned_model("model-2", "ft-2", "gpt-4", metrics={"acc": 0.95})
        manager.register_fine_tuned_model("model-3", "ft-3", "gpt-3.5-turbo", metrics={"acc": 0.88})

        models = manager.list_fine_tuned_models()
        assert len(models) == 3

        assert manager.get_fine_tuned_model("model-1").metrics["acc"] == 0.9
        assert manager.get_fine_tuned_model("model-2").metrics["acc"] == 0.95
        assert manager.get_fine_tuned_model("model-3").metrics["acc"] == 0.88
        print("    - Multiple models management OK")

    def test_fine_tuning_wrapper_switch_models(self):
        """测试wrapper切换不同模型"""
        fine_tuning = load_module('ft_edge_16', 'core/llm/fine_tuning.py')
        FineTuningWrapper = fine_tuning.FineTuningWrapper
        FineTuningManager = fine_tuning.FineTuningManager
        FineTuningStatus = fine_tuning.FineTuningStatus

        class MockLLM:
            async def generate(self, prompt, **kwargs):
                model = kwargs.get('model', 'base')
                return f"Response using {model}"

        manager = FineTuningManager(provider="openai")

        # 创建成功的job
        job = fine_tuning.FineTuningJob(
            id="success-job",
            model="gpt-3.5-turbo",
            status=FineTuningStatus.SUCCEEDED,
            fine_tuned_model="ft:gpt-3.5-turbo:my-model"
        )
        manager.jobs["success-job"] = job

        wrapper = FineTuningWrapper(base_llm=MockLLM(), fine_tuning_manager=manager)

        # 使用基础模型
        wrapper.use_base_model()
        assert wrapper.is_fine_tuned is False

        # 切换到微调模型
        result = wrapper.use_fine_tuned("success-job")
        assert result is True
        assert wrapper.is_fine_tuned is True
        assert wrapper.current_model_name == "ft:gpt-3.5-turbo:my-model"
        print("    - Wrapper switch models OK")

    def test_training_data_unicode_filename(self):
        """测试Unicode文件名处理"""
        fine_tuning = load_module('ft_edge_17', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager

        manager = FineTuningManager(provider="openai")

        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.jsonl',
            delete=False,
            encoding='utf-8',
            prefix='测试文件_'
        ) as f:
            f.write('{"messages": [{"role": "user", "content": "你好"}]}\n')
            temp_path = f.name

        try:
            result = manager.create_training_data(temp_path)
            assert result.record_count == 1
            assert '测试文件_' in result.file_name
            print("    - Unicode filename OK")
        finally:
            os.unlink(temp_path)

    def test_fine_tuning_api_list_jobs(self):
        """测试API列出所有任务"""
        fine_tuning = load_module('ft_edge_18', 'core/llm/fine_tuning.py')
        FineTuningAPI = fine_tuning.FineTuningAPI
        FineTuningStatus = fine_tuning.FineTuningStatus

        # 使用非openai provider避免API调用
        api = FineTuningAPI()
        api.manager.provider = "anthropic"  # 避免OpenAI API调用

        # 手动添加一些job
        job = fine_tuning.FineTuningJob(
            id="api-test-job",
            model="gpt-3.5-turbo",
            status=FineTuningStatus.PENDING
        )
        api.manager.jobs["api-test-job"] = job

        jobs = api.list_jobs()
        assert len(jobs) >= 1
        assert any(j["id"] == "api-test-job" for j in jobs)
        print("    - API list jobs OK")

    def test_manager_with_provider_case_insensitive(self):
        """测试provider大小写不敏感"""
        fine_tuning = load_module('ft_edge_19', 'core/llm/fine_tuning.py')
        FineTuningManager = fine_tuning.FineTuningManager

        manager1 = FineTuningManager(provider="OPENAI")
        manager2 = FineTuningManager(provider="openai")
        manager3 = FineTuningManager(provider="OpenAI")

        assert manager1.provider == "openai"
        assert manager2.provider == "openai"
        assert manager3.provider == "openai"
        print("    - Provider case insensitive OK")

    def test_job_status_map_all_statuses(self):
        """测试所有状态都能正确映射"""
        fine_tuning = load_module('ft_edge_20', 'core/llm/fine_tuning.py')
        FineTuningStatus = fine_tuning.FineTuningStatus

        status_map = {
            "pending": FineTuningStatus.PENDING,
            "running": FineTuningStatus.RUNNING,
            "succeeded": FineTuningStatus.SUCCEEDED,
            "failed": FineTuningStatus.FAILED,
            "cancelled": FineTuningStatus.CANCELLED
        }

        for api_status, internal_status in status_map.items():
            assert internal_status.value == api_status
        print("    - Status map OK")


if __name__ == "__main__":
    print("=" * 60)
    print("Fine-tuning Module Test")
    print("=" * 60)
    print()

    tests = [
        ("FineTuningStatus Enum", test_fine_tuning_status_enum),
        ("ModelVersion Enum", test_model_version_enum),
        ("TrainingData Creation", test_training_data_creation),
        ("FineTuningJob Creation", test_fine_tuning_job_creation),
        ("FineTuningJob to_dict", test_fine_tuning_job_to_dict),
        ("FineTunedModel Creation", test_fine_tuned_model_creation),
        ("FineTuningManager Init", test_fine_tuning_manager_init),
        ("Prepare Training Data", test_prepare_training_data),
        ("Create Training Data", test_create_training_data),
        ("Register Fine-tuned Model", test_register_fine_tuned_model),
        ("List Fine-tuned Models", test_list_fine_tuned_models),
        ("FineTuningWrapper", test_fine_tuning_wrapper),
        ("FineTuningAPI", test_fine_tuning_api),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"[{name}]")
        try:
            test_func()
            passed += 1
            print("    PASS")
        except AssertionError as e:
            print(f"    FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"    ERROR: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Result: {passed}/{passed+failed} passed")
    if failed > 0:
        print(f"Failed: {failed}")
    print("=" * 60)