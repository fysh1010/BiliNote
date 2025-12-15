from typing import Optional, Union

from openai import OpenAI

from app.utils.logger import get_logger

logging= get_logger(__name__)
class OpenAICompatibleProvider:
    def __init__(self, api_key: str, base_url: str, model: Union[str, None]=None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    @property
    def get_client(self):
        return self.client

    @staticmethod
    def test_connection(api_key: str, base_url: str, model_name: str | None = None) -> bool:
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            client.models.list()
            logging.info("连通性测试成功")
            return True
        except Exception as e:
            logging.info(f"连通性测试失败：{e}")
            try:
                if not model_name:
                    raise RuntimeError(f"Provider does not support /models; please add a model name and retry. Original error: {e}")
                client = OpenAI(api_key=api_key, base_url=base_url)
                client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=1,
                )
                logging.info("连通性测试成功")
                return True
            except Exception as e2:
                logging.info(f"连通性测试失败：{e2}")
                return False