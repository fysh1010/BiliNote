from fastapi.encoders import jsonable_encoder
import uuid

from app.db.models.providers import Provider
from app.db.provider_dao import (
    insert_provider,
    get_all_providers,
    get_provider_by_name,
    get_provider_by_id,
    update_provider,
    delete_provider as dao_delete_provider,
    get_enabled_providers,
)
from app.db.model_dao import delete_models_by_provider
from app.gpt.gpt_factory import GPTFactory
from app.models.model_config import ModelConfig


class ProviderService:

    @staticmethod
    def serialize_provider(row: Provider) -> dict:
        if not row:
            return None
        row = ProviderService.provider_to_dict(row)
        return {
            "id": row.get("id"),
            "name": row.get("name"),
            "logo": row.get("logo"),
            "type":row.get("type"),
            "enabled": row.get("enabled"),
            "base_url": row.get("base_url"),
            "api_key": row.get("api_key"),
            "created_at": jsonable_encoder(row.get("created_at")),
            # "name": row[1],
            # "logo": row[2],
            # "type": row[3],
            # "api_key": row[4],
            # "base_url": row[5],
            # "enabled": row[6],
            # "created_at": row[7],
        }
    @staticmethod
    def serialize_provider_safe(row: Provider) -> dict:
        if not row:
            return None
        row = ProviderService.provider_to_dict(row)

        return {
            "id": row.get("id"),
            "name": row.get("name"),
            "logo": row.get("logo"),
            "type":row.get("type"),
            "enabled": row.get("enabled"),
            "base_url": row.get("base_url"),
            "api_key":  ProviderService.mask_key(row.get("api_key")),
            "created_at": jsonable_encoder(row.get("created_at")),

            # "id": row[0],
            # "name": row[1],
            # "logo": row[2],
            # "type": row[3],
            # "api_key": ProviderService.mask_key(row[4]),
            # "base_url": row[5],
            # "enabled": row[6],
            # "created_at": row[7],
        }
    @staticmethod
    def mask_key(key: str) -> str:
        if not key or len(key) < 8:
            return '*' * len(key)
        return key[:4] + '*' * (len(key) - 8) + key[-4:]
    @staticmethod
    def add_provider( name: str, api_key: str, base_url: str, logo: str, type_: str, enabled: int = 1):
        try:
            # 使用传入的logo参数，如果为空则使用'custom'作为默认值
            if not logo or logo.strip() == '':
                logo = 'custom'

            # 如果已存在同名且非内置的供应商，则直接更新
            from app.db.provider_dao import get_provider_by_name as dao_get_provider_by_name
            from app.db.provider_dao import update_provider as dao_update_provider
            existing = dao_get_provider_by_name(name)
            if existing and existing.type != 'built-in':
                dao_update_provider(
                    existing.id,
                    name=name,
                    api_key=api_key,
                    base_url=base_url,
                    logo=logo,
                    type=type_,
                    enabled=enabled,
                )
                return existing.id

            id = str(uuid.uuid4())
            result = insert_provider(id, name, api_key, base_url, logo, type_, enabled)
            if not result:
                raise Exception('创建供应商失败')
            return result
        except Exception as  e:
            print('创建供应商失败',e)
            raise
    @staticmethod
    def provider_to_dict(p: Provider):
        return {
            "id": p.id,
            "name": p.name,
            "logo": p.logo,
            "type": p.type,
            "api_key": p.api_key,
            "base_url": p.base_url,
            "enabled": p.enabled,
            "created_at": p.created_at,
        }
    @staticmethod
    def get_all_providers():
        rows = get_all_providers()
        if rows is None:
            return []

        return [ProviderService.serialize_provider(row) for row in rows] if rows else []
    @staticmethod
    def get_all_providers_safe():
        rows = get_all_providers()

        return [ProviderService.serialize_provider(row) for row in rows] if (rows) else []
    @staticmethod
    def get_provider_by_name(name: str):
        from app.db.provider_dao import get_provider_by_name as dao_get_provider_by_name
        row = dao_get_provider_by_name(name)
        return ProviderService.serialize_provider(row)

    @staticmethod
    def get_provider_by_id(id: str):  # 已改为 str 类型
        from app.db.provider_dao import get_provider_by_id as dao_get_provider_by_id
        row = dao_get_provider_by_id(id)
        return ProviderService.serialize_provider(row)

    @staticmethod
    def get_provider_by_id_safe(id: str):  # 已改为 str 类型
        from app.db.provider_dao import get_provider_by_id as dao_get_provider_by_id
        row = dao_get_provider_by_id(id)
        return ProviderService.serialize_provider_safe(row)
            # all_models.extend(provider['models'])

    @staticmethod
    def update_provider(id: str, data: dict)->str | None:
        try:
            # 过滤掉空值
            filtered_data = {k: v for k, v in data.items() if v is not None and k != 'id'}
            print('更新模型供应商',filtered_data)
            from app.db.provider_dao import update_provider as dao_update_provider
            dao_update_provider(id, **filtered_data)
            return id

        except Exception as e:
            print('更新模型供应商失败：',e)
            raise

    @staticmethod
    def delete_provider(id: str):
        from app.db.provider_dao import get_provider_by_id as dao_get_provider_by_id
        provider = dao_get_provider_by_id(id)
        if not provider:
            return False

        # 内置供应商不允许删除
        if provider.type == 'built-in':
            raise ValueError('内置模型供应商不支持删除')

        # 删除关联模型
        delete_models_by_provider(id)
        dao_delete_provider(id)
        return True
