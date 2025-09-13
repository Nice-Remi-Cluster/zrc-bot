from pydantic import BaseModel


class Config(BaseModel):
    """Plugin Config Here"""

    diving_fish_developer_token: str

    lxns_base_url: str
    lxns_developer_token: str

    # LXNS OAuth 配置
    lxns_oauth_client_id: str
    lxns_oauth_client_secret: str

    maimai_arcade_chip_id: str
    maimai_arcade_aes_key: str
    maimai_arcade_aes_iv: str
    maimai_arcade_obfuscate_param: str

    maimai_arcade_proxy_host: str
    maimai_arcade_proxy_port: int
    maimai_arcade_proxy_username: str
    maimai_arcade_proxy_password: str
