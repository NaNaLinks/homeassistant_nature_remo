import logging
import voluptuous as vol
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .coordinator import NatureRemoCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_TOKEN = "token"
CONF_NAME = "name"
CONF_DEVICE_ID = "device_id"
CONF_APPLIANCE_ID = "appliance_id"

MODE_MAP = {
    HVACMode.COOL: "cool",
    HVACMode.HEAT: "warm",
    HVACMode.DRY: "dry",
    HVACMode.FAN_ONLY: "blow",
    HVACMode.AUTO: "auto",
}

PLATFORM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOKEN): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_APPLIANCE_ID): cv.string,
    }
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """
    UI設定からエアコンエンティティを追加.
    Add air conditioner entity from UI configuration.
    """
    _LOGGER.info("Nature Remo Climate: async_setup_entry called!")
    _LOGGER.debug(f"★[Climate]{hass.data[DOMAIN][entry.entry_id]}")
    _LOGGER.debug(f"config_entry.options: {entry.options}")

    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: NatureRemoCoordinator = data["coordinator"]
    api = data["api"]

    entities = []

    for appliance in coordinator.aircons.values():

        entity = NatureRemoClimate(
            coordinator=coordinator,
            appliance=appliance,
            device=appliance["device"],
            api=api,
            entry_id=entry.entry_id,  # [Issue#4] entry_idのみ保持してoptionsにアクセスする
        )
        entities.append(entity)

    if not entities:
        _LOGGER.warning("No climate appliances matched selected IDs.")

    async_add_entities(entities, True)


class NatureRemoClimate(ClimateEntity):
    """
    Nature Remoでエアコンを操作するエンティティ.
    Entity to control an air conditioner via Nature Remo.
    """

    def __init__(
        self,
        coordinator: NatureRemoCoordinator,
        appliance,
        device,
        api,
        entry_id: str = None,  # [Issue#4] entry_idのみ受け取る（hassはself.hassで参照）
    ) -> None:
        """エアコンの初期設定. / Initialize air conditioner settings."""
        _LOGGER.debug(f'[{appliance["name"]}]Start __init__')
        try:
            self._attr_unique_id = f"nature_remo_climate_{appliance["appliance_id"]}"
            self._attr_name = f"Nature Remo {appliance["name"]}"
            self._coordinator = coordinator
            self._appliance = appliance
            self._device = device
            self._appliance_id = appliance["appliance_id"]
            self._temperature = None
            self._humidity = None
            self._hvac_modes = [HVACMode.OFF]
            self._hvac_mode = HVACMode.OFF
            self._button = "power-off"
            self._api = api
            self._target_temperature = 25
            self._fan_mode = "auto"
            self._swing_mode = "auto"
            self._aircon_range_modes = {}

            # [Issue#4] entry_idを保持（optionsはself.hassから都度取得する）
            # self.hassはasync_added_to_hass()以降にHAフレームワークが自動セットする
            self._entry_id = entry_id

        except Exception as e:
            _LOGGER.error(f"Error initializing NatureRemoClimate: {e}")

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device["device_id"])},
            "name": self._device["name"],
            "manufacturer": "Nature",
            "model": self._device.get("firmware_version", "Nature Remo"),
        }

    @property
    def supported_features(self) -> int:
        """対応している機能を定義. / Define the features supported by this entity."""
        _LOGGER.debug(f"[{self._attr_name}] Start supported_features")
        support_feature = ClimateEntityFeature(0)
        if self.min_temp != 0.0 and self.max_temp != 0.0:
            support_feature = support_feature | ClimateEntityFeature.TARGET_TEMPERATURE
        if self.fan_modes:
            support_feature = support_feature | ClimateEntityFeature.FAN_MODE
        if self.swing_modes:
            support_feature = support_feature | ClimateEntityFeature.SWING_MODE

        _LOGGER.info(f"Nature Remo Climate support_feature: {support_feature}")
        return support_feature

    @property
    def target_temperature_step(self) -> float:
        """温度変更の刻み幅を設定. / Set the step size for temperature adjustment."""
        _LOGGER.debug(f"[{self._attr_name}] Start target_temperature_step")
        remo_mode = MODE_MAP.get(self._hvac_mode)
        temp_list = self._aircon_range_modes.get(remo_mode, {}).get("temp", [])
        temp_list = list(map(float, filter(None, temp_list)))

        if not temp_list:
            return 0.0

        differences = [
            temp_list[i + 1] - temp_list[i] for i in range(len(temp_list) - 1)
        ]

        step = 1.0
        if len(set(differences)) == 1:
            step = differences[0]
        _LOGGER.debug(f"target_temperature_step: {step}")
        return step

    @property
    def min_temp(self):
        """設定可能な最低温度. / Return the minimum temperature that can be set."""
        _LOGGER.debug(f"[{self._attr_name}] Start min_temp")
        remo_mode = MODE_MAP.get(self._hvac_mode)
        temp_list = self._aircon_range_modes.get(remo_mode, {}).get("temp", [])
        temp_list = list(map(float, filter(None, temp_list)))
        if not temp_list:
            return 0.0

        _LOGGER.debug(f"min_temp: {min(temp_list)}")
        return min(temp_list)

    @property
    def max_temp(self):
        """設定可能な最高温度. / Return the maximum temperature that can be set."""
        remo_mode = MODE_MAP.get(self._hvac_mode)
        temp_list = self._aircon_range_modes.get(remo_mode, {}).get("temp", [])
        temp_list = list(map(float, filter(None, temp_list)))
        if not temp_list:
            return 0.0

        _LOGGER.debug(f"max_temp: {max(temp_list)}")
        return max(temp_list)

    @property
    def current_temperature(self) -> float | None:
        """現在の室温を返す / Return the current room temperature."""
        return self._temperature

    @property
    def current_humidity(self) -> int | None:
        """現在の湿度を返す / Return the current room humidity."""
        return self._humidity

    @property
    def name(self):
        """エアコンの表示名を返す. / Return the display name of the air conditioner."""
        return self._attr_name

    @property
    def temperature_unit(self) -> str:
        """温度の単位を取得. / Get the temperature unit used by the device."""
        return UnitOfTemperature.CELSIUS

    @property
    def hvac_mode(self):
        """現在の動作モード. / Current operation mode of the air conditioner."""
        if self._button == "power-off":
            return HVACMode.OFF
        return self._hvac_mode

    @property
    def hvac_modes(self):
        """サポートするモード. / List of supported HVAC modes."""
        return self._hvac_modes

    @property
    def fan_modes(self) -> list[str] | None:
        """設定可能な風量のリスト. / List of available fan modes."""
        remo_mode = MODE_MAP.get(self._hvac_mode)
        return self._aircon_range_modes.get(remo_mode, {}).get("vol", [])

    @property
    def swing_modes(self) -> list[str] | None:
        """設定可能な風向きのリスト. / List of available swing modes."""
        remo_mode = MODE_MAP.get(self._hvac_mode)
        return self._aircon_range_modes.get(remo_mode, {}).get("dir", [])

    @property
    def target_temperature(self) -> float | None:
        """現在の目標温度を取得. / Get the current target temperature."""
        return self._target_temperature

    @property
    def fan_mode(self) -> str | None:
        """現在の風量を返す. / Return the current fan mode."""
        return self._fan_mode

    @property
    def swing_mode(self) -> str | None:
        """現在の風向きを返す. / Return the current swing mode."""
        return self._swing_mode

    def _get_external_sensor_value(self, sensor_type: str) -> float | None:
        """
        [Issue#4] 外部センサーエンティティから値を取得する.
        Get value from external sensor entity if configured.

        Args:
            sensor_type: "temperature" または "humidity"
        Returns:
            外部センサーの値（未設定またはエラー時はNone）

        Note:
            self.hassはHAフレームワークがasync_added_to_hass()以降に自動セットする。
            __init__時点ではNoneのため、このメソッドはasync_added_to_hass()以降に呼ぶこと。
        """
        # [Issue#4] self.hassはHAフレームワークが自動セットするプロパティを使用
        if self.hass is None or self._entry_id is None:
            _LOGGER.debug(
                f"[{self._attr_name}] [{sensor_type}] self.hass={self.hass}, "
                f"self._entry_id={self._entry_id} → スキップ / skipped"
            )
            return None

        # [Issue#4] config_entriesからoptionsを都度取得（最新の設定を参照できる）
        entry = self.hass.config_entries.async_get_entry(self._entry_id)
        if entry is None:
            _LOGGER.warning(
                f"[{self._attr_name}] entry_id '{self._entry_id}' のConfigEntryが見つかりません。"
                f" / ConfigEntry not found for entry_id '{self._entry_id}'."
            )
            return None

        device_id = self._device["device_id"]
        option_key = f"external_{sensor_type}_{device_id}"
        entity_id = entry.options.get(option_key)

        _LOGGER.debug(
            f"[{self._attr_name}] [{sensor_type}] "
            f"device_id='{device_id}' / "
            f"option_key='{option_key}' / "
            f"entity_id='{entity_id}' / "
            f"options={entry.options}"
        )

        if not entity_id:
            _LOGGER.debug(
                f"[{self._attr_name}] [{sensor_type}] "
                f"外部センサー未設定のためNature Remoの値を使用 / "
                f"No external sensor configured, using Nature Remo value"
            )
            return None

        state = self.hass.states.get(entity_id)
        if state is None:
            _LOGGER.warning(
                f"[{self._attr_name}] 外部{sensor_type}センサー '{entity_id}' の状態が取得できません。"
                f" / External {sensor_type} sensor '{entity_id}' state not found."
            )
            return None

        try:
            value = float(state.state)
            _LOGGER.debug(
                f"[{self._attr_name}] 外部{sensor_type}センサー '{entity_id}' から値を取得: {value}"
                f" / Got {sensor_type} value {value} from external sensor '{entity_id}'"
            )
            return value
        except (ValueError, TypeError):
            _LOGGER.warning(
                f"[{self._attr_name}] 外部{sensor_type}センサー '{entity_id}' の値が無効です: {state.state}"
                f" / Invalid {sensor_type} value from external sensor '{entity_id}': {state.state}"
            )
            return None

    def update_status(self) -> None:
        """
        コーディネーターで取得した値に更新する.
        Update values using the data from the coordinator.
        """
        _LOGGER.debug(f"[{self._attr_name}] Start update_status.")
        appliance = self._coordinator.data.get(self._appliance_id, {})

        # [Issue#4] 外部温度センサーが設定されていればそちらを優先して使用する
        # If external temperature sensor is configured, use it preferentially
        external_temperature = self._get_external_sensor_value("temperature")
        if external_temperature is not None:
            self._temperature = external_temperature
            _LOGGER.debug(
                f"[{self._attr_name}] 外部温度センサーから室温を取得: {self._temperature}℃"
                f" / Using external temperature sensor: {self._temperature}℃"
            )

        # [Issue#4] 外部湿度センサーが設定されていればそちらを優先して使用する
        # If external humidity sensor is configured, use it preferentially
        external_humidity = self._get_external_sensor_value("humidity")
        if external_humidity is not None:
            self._humidity = external_humidity
            _LOGGER.debug(
                f"[{self._attr_name}] 外部湿度センサーから湿度を取得: {self._humidity}%"
                f" / Using external humidity sensor: {self._humidity}%"
            )

        # 外部センサー未設定の場合はNature Remoデバイスの値を使用（従来通り）
        # Fall back to Nature Remo device sensor if external sensors are not configured
        device_id = self._device["device_id"]
        device_data = self._coordinator.devices.get(device_id)  # KeyError対策でgetを使用
        if device_data is None:
            _LOGGER.warning(
                f"[{self._attr_name}] デバイス '{device_id}' がcoordinatorのdevicesに見つかりません。"
                f" / Device '{device_id}' not found in coordinator devices."
            )
        else:
            device_events = device_data.get("events", {})
            # 外部温度センサー未設定の場合のみNature Remoの値を使用
            if external_temperature is None:
                if "te" in device_events:
                    self._temperature = device_events["te"].get("val")
                    _LOGGER.debug(
                        f"[{self._attr_name}] Nature Remoデバイスから室温を取得: {self._temperature}℃"
                        f" / Using Nature Remo device temperature: {self._temperature}℃"
                    )
            # 外部湿度センサー未設定の場合のみNature Remoの値を使用
            if external_humidity is None:
                if "hu" in device_events:
                    self._humidity = device_events["hu"].get("val")
                    _LOGGER.debug(
                        f"[{self._attr_name}] Nature Remoデバイスから湿度を取得: {self._humidity}%"
                        f" / Using Nature Remo device humidity: {self._humidity}%"
                    )

        # settingsから取得できる情報
        if appliance and "settings" in appliance:
            _LOGGER.info("***Nature Remo Settings: %s", appliance["settings"])
            # 動作モード
            self._hvac_mode = self.get_remo_mode_to_hvac_mode(
                appliance["settings"].get("mode", "")
            )
            # ボタン（OFFボタン）
            self._button = appliance["settings"].get("button", "")

            # 目標温度
            temp = appliance["settings"].get("temp", "20.0")
            try:
                self._target_temperature = float(temp)
            except (ValueError, TypeError):
                self._target_temperature = 0.0

            # 風量
            self._fan_mode = appliance["settings"].get("vol", "auto")
            # 風向き
            self._swing_mode = appliance["settings"].get("dir", "auto")

        # aircon_range_mode
        if appliance and "aircon" in appliance:
            self._aircon_range_modes = (
                appliance["aircon"].get("range", {}).get("modes", {})
            )
            if self._aircon_range_modes:
                set_range_modes = [HVACMode.OFF]
                if self._aircon_range_modes.get("cool", {}):
                    set_range_modes.append(HVACMode.COOL)
                if self._aircon_range_modes.get("dry", {}):
                    set_range_modes.append(HVACMode.DRY)
                if self._aircon_range_modes.get("warm", {}):
                    set_range_modes.append(HVACMode.HEAT)
                if self._aircon_range_modes.get("blow", {}):
                    set_range_modes.append(HVACMode.FAN_ONLY)
                if self._aircon_range_modes.get("auto", {}):
                    set_range_modes.append(HVACMode.AUTO)
                self._hvac_modes = set_range_modes

        self.async_write_ha_state()

    def get_remo_mode_to_hvac_mode(self, remo_mode) -> HVACMode | None:
        """
        Nature Remoの動作モードをHomeAssistantの動作モードに変換する.
        Convert Nature Remo operation mode to Home Assistant HVAC mode.
        """
        return next(
            (key for key, value in MODE_MAP.items() if value == remo_mode),
            None,
        )

    async def async_added_to_hass(self):
        """
        エンティティがHome Assistantに追加されたら更新をトリガー.
        Trigger update when the entity is added to Home Assistant.

        Note:
            このメソッドが呼ばれた時点でself.hassがHAフレームワークによりセットされる。
            そのため_get_external_sensor_value()はここ以降で正しく動作する。
        """
        _LOGGER.info(
            f"[{self._attr_name}] async_added_to_hass: Climate entity complete setup"
        )
        self.async_on_remove(self._coordinator.async_add_listener(self.update_status))
        self.update_status()
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """エアコンのモードを変更. / Change the operation mode of the air conditioner."""
        _LOGGER.info("Setting HVAC mode: %s", hvac_mode)
        if hvac_mode not in self.hvac_modes:
            _LOGGER.warning("Unsupported HVAC mode: %s", hvac_mode)
            return

        if hvac_mode == HVACMode.OFF:
            payload = {"button": "power-off"}
            self._button = "power-off"
        else:
            operation_mode = MODE_MAP.get(hvac_mode)
            payload = {"operation_mode": operation_mode}
            self._button = ""
            self._hvac_mode = hvac_mode

        response = await self._api.send_command_climate(payload, self._appliance_id)
        _LOGGER.info("Set HVACMode: %s", response)
        self._hvac_mode = self.get_remo_mode_to_hvac_mode(response.get("mode", ""))
        if self._hvac_mode is HVACMode.FAN_ONLY:
            temp = "0.0"
        else:
            temp = response.get("temp", "25.0")
        self._target_temperature = float(temp)
        self._fan_mode = response.get("vol", "auto")
        self._swing_mode = response.get("dir", "auto")
        self._button = response.get("button", "")

        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """エアコンの温度を変更. / Change the temperature setting of the air conditioner."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            _LOGGER.warning("温度が指定されていません！")
            return

        operation_mode = MODE_MAP.get(self._hvac_mode)
        if operation_mode is None:
            _LOGGER.error("Invalid HVAC mode: %s", self._hvac_mode)
            return

        _LOGGER.debug("Setting temperature to: %s", temperature)

        set_temperature = self.format_temperature(temperature)
        payload = {
            "operation_mode": operation_mode,
            "temperature": set_temperature,
        }

        await self._api.send_command_climate(payload, self._appliance_id)
        self._target_temperature = temperature
        self._button = ""
        self.async_write_ha_state()

    def format_temperature(self, value: float) -> str:
        if value.is_integer():
            return str(int(value))
        else:
            return str(value)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """風量を変更. / Change the fan mode."""
        operation_mode = MODE_MAP.get(self._hvac_mode)
        if operation_mode is None:
            _LOGGER.error("Invalid HVAC mode: %s", self._hvac_mode)
            return

        payload = {
            "operation_mode": operation_mode,
            "air_volume": fan_mode,
        }

        await self._api.send_command_climate(payload, self._appliance_id)
        self._fan_mode = fan_mode
        self._button = ""
        self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """風向きを変更. / Change the swing mode."""
        operation_mode = MODE_MAP.get(self._hvac_mode)
        if operation_mode is None:
            _LOGGER.error("Invalid HVAC mode: %s", self._hvac_mode)
            return

        payload = {
            "operation_mode": operation_mode,
            "air_direction": swing_mode,
        }

        await self._api.send_command_climate(payload, self._appliance_id)
        self._swing_mode = swing_mode
        self._button = ""
        self.async_write_ha_state()