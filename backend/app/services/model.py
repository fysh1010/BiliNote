

from typing import Any

from app.db.model_dao import insert_model, get_all_models, get_model_by_provider_and_name, delete_model
from app.db.provider_dao import get_enabled_providers
from app.enmus.exception import ProviderErrorEnum
from app.exceptions.provider import ProviderError
from app.gpt.gpt_factory import GPTFactory
from app.gpt.provider.OpenAI_compatible_provider import OpenAICompatibleProvider
from app.models.model_config import ModelConfig
from app.services.provider import ProviderService
from app.utils.logger import get_logger

logger=get_logger(__name__)
class ModelService:

    @staticmethod
    def _normalize_model_items(models: Any) -> list[dict]:
        items: list[Any] = []

        if models is None:
            items = []
        elif hasattr(models, "data"):
            try:
                items = list(getattr(models, "data"))
            except TypeError:
                items = []
        elif isinstance(models, dict):
            if isinstance(models.get("data"), list):
                items = models.get("data")
            elif isinstance(models.get("models"), list):
                items = models.get("models")
            else:
                items = []
        elif isinstance(models, list):
            items = models
        else:
            items = [models]

        normalized: list[dict] = []
        for m in items:
            model_id: str | None = None
            if isinstance(m, str):
                model_id = m
            elif isinstance(m, dict):
                model_id = m.get("id") or m.get("model") or m.get("name")
            else:
                model_id = getattr(m, "id", None) or getattr(m, "model", None) or getattr(m, "name", None)

            if model_id:
                normalized.append({"id": str(model_id)})

        return normalized

    @staticmethod
    def _build_model_config(provider: dict) -> ModelConfig:
        return ModelConfig(
            api_key=provider["api_key"],
            base_url=provider["base_url"],
            provider=provider["name"],
            model_name='',
            name=provider["name"],
        )

    @staticmethod
    def get_model_list(provider_id: int, verbose: bool = False):
        provider = ProviderService.get_provider_by_id(provider_id)
        if not provider:
            return []

        try:
            config = ModelService._build_model_config(provider)
            gpt = GPTFactory().from_config(config)
            models = gpt.list_models()
            if verbose:
                print(f"[{provider['name']}] 模型列表: {models}")
            return models
        except Exception as e:
            print(f"[{provider['name']}] 获取模型失败: {e}")
            return []

    @staticmethod
    def get_all_models(verbose: bool = False):
        try:
            raw_models = get_all_models()
            if verbose:
                print(f"所有模型列表: {raw_models}")
            return ModelService._format_models(raw_models)
        except Exception as e:
            print(f"获取所有模型失败: {e}")
            return []
    @staticmethod
    def get_all_models_safe(verbose: bool = False):
        try:
            raw_models = get_all_models()
            if verbose:
                print(f"所有模型列表: {raw_models}")
            return ModelService._format_models(raw_models)
        except Exception as e:
            print(f"获取所有模型失败: {e}")
            return []
    @staticmethod
    def _format_models(raw_models: list) -> list:
        """
        格式化模型列表
        """
        formatted = []
        for model in raw_models:
            formatted.append({
                "id": model.get("id"),
                "provider_id": model.get("provider_id"),
                "model_name": model.get("model_name"),
                "created_at": model.get("created_at", None),  # 如果有created_at字段
            })
        return formatted
    @staticmethod
    def get_enabled_models_by_provider( provider_id: str|int,):
        from app.db.model_dao import get_models_by_provider

        all_models = get_models_by_provider(provider_id)
        enabled_models = all_models
        return enabled_models
    @staticmethod
    def get_all_models_by_id(provider_id: str, verbose: bool = False):
        provider = ProviderService.get_provider_by_id(provider_id)
        if not provider:
            raise ValueError(f"Provider not found: {provider_id}")

        try:
            config = ModelService._build_model_config(provider)
            gpt = GPTFactory().from_config(config)
            models = gpt.list_models()

            model_list = {"models": ModelService._normalize_model_items(models)}
            logger.info(f"[{provider['name']}] 获取模型成功")
            return model_list
        except Exception as e:
            logger.error(f"[{provider.get('name', provider_id)}] 获取模型失败: {e}")
            return {"models": []}
    @staticmethod
    def connect_test(id: str) -> bool:

        provider = ProviderService.get_provider_by_id(id)

        if provider:
            if not provider.get('api_key'):
                raise ProviderError(code=ProviderErrorEnum.NOT_FOUND.code, message=ProviderErrorEnum.NOT_FOUND.message)
            model_name = None
            try:
                enabled_models = ModelService.get_enabled_models_by_provider(id)
                if enabled_models and isinstance(enabled_models, list):
                    model_name = enabled_models[0].get('model_name')
            except Exception:
                model_name = None

            try:
                result =  OpenAICompatibleProvider.test_connection(
                    api_key=provider.get('api_key'),
                    base_url=provider.get('base_url'),
                    model_name=model_name,
                )
            except Exception as e:
                raise ProviderError(code=ProviderErrorEnum.CONNECTION_TEST_FAILED.code, message=str(e))

            if result:
                return True
            raise ProviderError(code=ProviderErrorEnum.CONNECTION_TEST_FAILED.code, message=ProviderErrorEnum.CONNECTION_TEST_FAILED.message)

        raise ProviderError(code=ProviderErrorEnum.NOT_FOUND.code, message=ProviderErrorEnum.NOT_FOUND.message)



    @staticmethod
    def delete_model_by_id( model_id: int) -> bool:
        try:
            delete_model(model_id)
            return True
        except Exception as e:
            print(f"[{model_id}] <UNK>: {e}")
            return False
    @staticmethod
    def add_new_model(provider_id: str, model_name: str) -> bool:
        try:
            # 先查供应商是否存在
            provider = ProviderService.get_provider_by_id(provider_id)
            if not provider:
                print(f"供应商ID {provider_id} 不存在，无法添加模型")
                return False

            # 查询是否已存在同名模型
            existing = get_model_by_provider_and_name(provider_id, model_name)
            if existing:
                print(f"模型 {model_name} 已存在于供应商ID {provider_id} 下，跳过插入")
                return False

            # 插入模型
            insert_model(provider_id=provider_id, model_name=model_name)
            print(f"模型 {model_name} 已成功添加到供应商ID {provider_id}")
            return True
        except Exception as e:
            print(f"添加模型失败: {e}")
            return False

if __name__ == '__main__':
    # 单个 Provider 测试
    print(ModelService.get_model_list(1, verbose=True))

    # 所有 Provider 模型测试
    # print(ModelService.get_all_models(verbose=True))
