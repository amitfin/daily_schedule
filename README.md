# Daily Schedule

[![HACS Badge](https://img.shields.io/badge/HACS-Default-31A9F4.svg?style=for-the-badge)](https://github.com/hacs/integration)

[![GitHub Release](https://img.shields.io/github/release/amitfin/daily_schedule.svg?style=for-the-badge&color=blue)](https://github.com/amitfin/daily_schedule/releases) ![Analytics](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=blue&label=Analytics&suffix=%20Installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.daily_schedule.total)

![Project Maintenance](https://img.shields.io/badge/maintainer-Amit%20Finkelstein-blue.svg?style=for-the-badge)

The Daily Schedule integration provides a binary sensor that gets its `on` / `off` state according to the user-defined schedule of time ranges.

_There is a corresponding [Lovelace card](https://github.com/amitfin/lovelace-daily-schedule-card) which should be used for configuration. To open the card installation page inside HACS click [here](https://my.home-assistant.io/redirect/hacs_repository/?owner=amitfin&repository=lovelace-daily-schedule-card&category=plugin)._

Automation rules can be built with the daily schedule entities as demonstrated [here](https://youtu.be/5toly_W7fUU).

_Note: The built-in [Schedule integration](https://www.home-assistant.io/integrations/schedule/) can be used when a weekly schedule is needed._

## Install

[HACS](https://hacs.xyz/) is the preferred and easier way to install the component. When HACS is installed, the integration can be installed using this My button:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=amitfin&repository=daily_schedule&category=integration)

Otherwise, download `daily_schedule.zip` from the [latest release](https://github.com/amitfin/daily_schedule/releases), extract and copy the content into `custom_components/daily_schedule` directory.

📌 **Home Assistant core restart** is required once the integration files are copied (either by HACS or manually).

## Create Daily Schedule

Use this link:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=daily_schedule)

Or, in the Home Assistant UI go through the following path:

[![Open your Home Assistant instance and show your settings menu.](https://my.home-assistant.io/badges/config.svg)](https://my.home-assistant.io/redirect/config/)

[![Open your Home Assistant instance and show your devices.](https://my.home-assistant.io/badges/devices.svg)](https://my.home-assistant.io/redirect/devices/)

[![Open your Home Assistant instance and show your helper entities.](https://my.home-assistant.io/badges/helpers.svg)](https://my.home-assistant.io/redirect/helpers/)

=> Click "+ Create helper" button and search for "Daily Schedule".

## Usage (Lovelace Card)

<img width="601" alt="image" src="https://github.com/user-attachments/assets/44dee96b-72e3-4bbe-81d4-b88c3ce9cb63" />
<br>
<img width="342" src="https://github.com/user-attachments/assets/3aa2fbc2-f8eb-4395-80c1-f73ca07a4812" />
<br>
<img src="https://github.com/user-attachments/assets/7466f370-f22c-49dc-888a-35233d55f065" width="534"/>

## Time Ranges

Each range has `from` and `to`. If the `to` is less than or equal `from` it's treated as time in the following day. One interesting case is when `from` equals `to`. This type of range covers the whole day (always on).

There are 3 ways to specify time:
1. A fixed time (e.g. 12:30).
2. Sunset with an optional negative or positive minutes offset.
3. Sunrise with an optional negative or positive minutes offset.

## Attributes

The binary sensor has the following attributes:
1. `Schedule`: the list of `on` time ranges as provided by the user.
2. `Effective schedule`: the actual `on` time ranges: (1) disabled ranges are ignored, (2) the user-provided ranges are merged and duplications are removed. This list doesn't include overlapping or adjusting ranges.
3. `Next toggle`: the next time when the binary sensor is going to change its state.
4. `Next toggles`: a list with the 4 next times when the binary sensor is going to change its state. The 1st element is identical to `Next toggle`.

## `set` Action

`daily_schedule.set` action can be used to configure the time ranges. Here is a YAML-mode example, although it's recommended to use the UI-mode:

```
action: daily_schedule.set
data:
  schedule:
    - from: "↓-30"
      to: "22:00"
target:
  entity_id: binary_sensor.backyard_lights
```

The format of `from` and `to` can be one of the 3 options:
1. ***Absolute time***: a 24h time in [this format](https://docs.python.org/3/library/datetime.html#datetime.time.fromisoformat).
2. ***Sunset***: start with "↓" and can have an optional positive or negative offset in minutes. For example: "↓", "↓-20", "↓+30".
3. ***Sunrise***: start with "↑" and can have an optional positive or negative offset in minutes.

Typically, there is no need to use this action directly since it's been used by the [Lovelace card](https://github.com/amitfin/lovelace-daily-schedule-card).

Note: there is no corresponding `get`. The data already exists as attributes:

```
{{ state_attr('binary_sensor.backyard_lights', 'schedule') }}
{{ state_attr('binary_sensor.backyard_lights', 'effective_schedule') }}
```

## Additional Cards

[Timer Bar Card](https://github.com/rianadon/timer-bar-card) supports this integration. ```end_time``` must be configured as follow:
```
end_time:
  attribute: next_toggle
```
By default it countdowns the time till the end of the current time range. ```active_state``` can be used for counting down the time to the beginning of the next range (instead):
```
active_state: 'off'
```

## UTC Option

When UTC option is set (not the default), the time should be expressed in [UTC](https://en.wikipedia.org/wiki/Coordinated_Universal_Time) instead of local time. This option can be used when absolute time is needed, which is not impacted by daylight saving changes throughout the year.
This is an advanced option that should not be used in the majority of the use cases. It should be used only if there is a very concrete reason to do so.

## Skip-Reversed Option

When enabled (disabled by default), this option ignores any time range where the `to` time is earlier than or equal to the `from` time. This behavior is dynamic. For example, a range defined as sunrise → 7:00 AM may become reversed during parts of the year if sunrise occurs after 7:00 AM. In such cases, the range is applied only when sunrise is earlier than 7:00 AM, and automatically skipped when sunrise is at 7:00 AM or later.

## Removing the Integration

1. **Delete the configuration:**
   - Open the integration page ([my-link](https://my.home-assistant.io/redirect/integration/?domain=daily_schedule)). Delete all helper entities by clicking the 3‑dot menu (⋮), and selecting **Delete**.

2. **Remove the integration files:**
   - If the integration was installed via **HACS**, follow the [official HACS removal instructions](https://www.hacs.xyz/docs/use/repositories/dashboard/#removing-a-repository).
   - Otherwise, manually delete the integration’s folder `custom_components/daily_schedule`.

📌 A **Home Assistant core restart** is required to fully apply the removal.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

