import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
import voluptuous as vol
from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)


class NatureRemoOptionsFlowHandler(config_entries.OptionsFlow):
    """
    Nature Remo のオプション設定フローを定義する.
    Defines the options flow for Nature Remo integration.
    """

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            result = {}
            for label, value in user_input.items():
                # 特別なキー名変換があるかどうかチェック
                if label in self.special_key_map:
                    result[self.special_key_map[label]] = value
                elif label in self.device_id_map:
                    result[self.device_id_map[label]] = value

            lang = self.hass.config.language
            if lang == "ja":
                title = "再読み込みが必要です"
                message = "Nature Remoの統合を再読み込みしてください。"
            else:
                title = "Reload Required"
                message = "Please reload the Nature Remo integration to apply changes."

            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": title,
                    "message": message,
                    "notification_id": "nature_remo_reload_needed",
                },
                blocking=True,
            )

            return self.async_create_entry(title="", data=result)

        device_registry = async_get_device_registry(self.hass)
        devices = [
            dev
            for dev in device_registry.devices.values()
            if dev.config_entries and self.config_entry.entry_id in dev.config_entries
        ]

        options = self.config_entry.options

        lang = self.hass.config.language
        if lang == "ja":
            interval_label = "更新間隔（秒）"
            ip_label_suffix = "：IPアドレス"
        else:
            interval_label = "Update Interval (seconds)"
            ip_label_suffix = ": IP Address"

        self.special_key_map = {interval_label: "update_interval"}
        self.device_id_map = {}

        interval_default = options.get("update_interval", 60)
        data_schema = {
            vol.Optional(interval_label, default=interval_default): vol.In(
                [30, 60, 90]
            ),
        }

        for device in devices:
            name = device.name_by_user or device.name or "Unknown Device"
            label = f"{name}{ip_label_suffix}"
            key = device.id
            self.device_id_map[label] = key
            data_schema[vol.Optional(label, default=options.get(key, ""))] = str

        return self.async_show_form(step_id="init", data_schema=vol.Schema(data_schema))
