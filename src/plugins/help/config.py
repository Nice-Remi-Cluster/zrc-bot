from typing import Union

from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    coze_api_token: str = ""
    coze_workflow_id_help: Union[str, int] = ""

    @property
    def coze_workflow_id_help_str(self) -> str:
        return str(self.coze_workflow_id_help)


