# Nature Remo - Home Assistant Custom Integration

⭐ If this integration helps you, please consider giving it a star on GitHub!

📄 日本語版のREADMEはこちら 👉 [README_ja.md](README_ja.md)

This is a custom integration for linking Nature Remo devices with Home Assistant.  
It enables you to control appliances like air conditioners and lights, and monitor temperature, humidity, and more directly in your smart home setup.

---

## ⚠️ Disclaimer
This is an **unofficial** integration and is not affiliated with Nature Inc. or Home Assistant.  
Please use this integration **at your own risk**.

---

## Features

- Control appliances (air conditioners, lights) registered to Nature Remo
- Retrieve temperature, humidity, illuminance, and motion sensor data
- Access smart meter data (consumption, generation, instant power) via Nature Remo E / E Lite
- Control lighting modes using custom service calls
- Send IR commands using remote entities created from defined signals

---

## Installation (via HACS)

Click the button below to easily add this repository to HACS.

[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=NaNaLinks/homeassistant_nature_remo&category=integration)

1. Open HACS in Home Assistant
2. Click the menu (⋮) in the top right corner
3. Select "Custom repositories"
4. Add this repository URL:
   https://github.com/NaNaLinks/homeassistant_nature_remo  
   Category: Integration
5. Install "Nature Remo"
6. Restart Home Assistant

---

## Installation (Manual)

1. Download or clone this repository and place it in the following path:

```
<config directory>/custom_components/nature_remo/
```

2. Restart Home Assistant.

---

## Setup Instructions

1. Go to *Settings → Devices & Services → Add Integration* and search for `Nature Remo`
2. Enter your access token (API key) and integration name
   - You can issue an API token at [Nature Official Site](https://home.nature.global)
3. Your registered appliances will be automatically imported as entities

---

## Options

- You can set the update interval (in seconds)
  - Default: `60 seconds`

⚠️ Nature Remo Cloud API has rate limits.  
Setting a very short update interval may cause the integration to reach the API request limit.

---

## Supported Entities

| Type    | Description                                                        |
|---------|--------------------------------------------------------------------|
| climate | Control air conditioners (cooling, heating, dry)                   |
| light   | Control lights (on/off, mode selection)                            |
| sensor  | Temperature, humidity, illuminance, motion, power (buy/sell)      |
| remote  | Send infrared signals defined as "signals" for IR/AC/LIGHT types  |

*Additional entities may be supported in future updates.*

---

## Sample: Using Remote Entities

This integration supports `remote` entities generated from Nature Remo's defined `signals`. These entities allow you to send IR commands directly from Home Assistant.

### Example: Service Call

You can call a signal like this using `remote.send_command`:

```yaml
service: remote.send_command
target:
  entity_id: remote.living_room_remote  # Your remote entity ID
data:
  command: "Power On"  # The name of the signal as defined in Remo
```

---

## Author

- Author: [@nanosns](https://github.com/nanosns) (NaNaRin)
- Project: [@NaNaLinks](https://github.com/NaNaLinks)
- Socials: [note](https://note.com/nanomana)

---

## License

MIT License