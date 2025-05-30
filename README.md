# Daily Schedule

[![HACS Badge](https://img.shields.io/badge/HACS-Default-31A9F4.svg?style=for-the-badge)](https://github.com/hacs/integration)

[![GitHub Release](https://img.shields.io/github/release/amitfin/daily_schedule.svg?style=for-the-badge&color=blue)](https://github.com/amitfin/daily_schedule/releases) ![Analytics](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=blue&label=Analytics&suffix=%20Installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.daily_schedule.total)

![Project Maintenance](https://img.shields.io/badge/maintainer-Amit%20Finkelstein-blue.svg?style=for-the-badge)

The Daily Schedule integration provides a binary sensor that gets its `on` / `off` state according to the user-defined schedule of time ranges.

_There is a corresponding [Lovelace card](https://github.com/amitfin/lovelace-daily-schedule-card) which should be used for configuration. To open the card installation page inside HACS click [here](https://my.home-assistant.io/redirect/hacs_repository/?owner=amitfin&repository=lovelace-daily-schedule-card&category=plugin)._

Automation rules can be built with the daily schedule entities as demonstrated [here](https://youtu.be/5toly_W7fUU).

_Note: The built-in [Schedule integration](https://www.home-assistant.io/integrations/schedule/) can be used when a weekly schedule is needed._

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
<img width="342" src="https://github.com/user-attachments/assets/dbaf02e2-7bed-48d3-97cf-cc767ea93691" />
<br>
<img src="https://github.com/user-attachments/assets/7466f370-f22c-49dc-888a-35233d55f065" width="534"/>

## Time Ranges

Each range has `from` and `to`. If the `to` is less than or equal `from` it's treated as time in the following day. One interesting case is when `from` equals `to`. This type of range covers the whole day (always on).

There are 3 ways to specify time:
1. A fixed time (e.g. 12:30).
2. Sunrise with an optional negative / positive offset.
3. Sunset with an optional negative / positive offset.

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

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)
