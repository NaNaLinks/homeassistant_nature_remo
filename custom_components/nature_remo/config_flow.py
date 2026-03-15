from __future__ import annotations

import logging
import voluptuous as vol
from typing import Any
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN
from .options_flow import NatureRemoOptionsFlowHandler

_LOGGER = logging.getLogger(__name__)

# APIキー入力用のスキーマ
API_SCHEMA = vol.Schema(
    {vol.Optional("name", default="Nature Remo"): str, vol.Required("api_key"): str}
)


class NatureRemoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Nature Remo 統合のセットアップフロー。
    Setup flow for the Nature Remo integration.
    """

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        self.api_key: str = ""
        self.appliances: list[dict[str, Any]] = []

    # ユーザーにAPIキーを入力してもらう
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """ユーザー入力によるセットアップ初期ステップ。"""
        if user_input is not None:
            # 入力されたAPIキーを保持
            self.api_key = user_input["api_key"]
            self.name = user_input.get("name", "Nature Remo")

            return self.async_create_entry(
                title=self.name, data={"api_key": self.api_key}
            )

        # APIキー入力フォームを表示
        return self.async_show_form(step_id="user", data_schema=API_SCHEMA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NatureRemoOptionsFlowHandler()
