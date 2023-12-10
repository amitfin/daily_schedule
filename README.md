# Daily Schedule

[![HACS Badge](https://img.shields.io/badge/HACS-Default-31A9F4.svg?style=for-the-badge)](https://github.com/hacs/integration)

[![GitHub Release](https://img.shields.io/github/release/amitfin/daily_schedule.svg?style=for-the-badge&color=blue)](https://github.com/amitfin/daily_schedule/releases) ![Analytics](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=blue&label=Analytics&suffix=%20Installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.daily_schedule.total)

![Project Maintenance](https://img.shields.io/badge/maintainer-Amit%20Finkelstein-blue.svg?style=for-the-badge)

The Daily Schedule integration provides a binary sensor that gets its ON/OFF state according to the user-defined schedule.

_There is a corresponding [Lovelace card](https://github.com/amitfin/lovelace-daily-schedule-card) with an optimized view and simplified editing capabilities. To open the card installation page inside HACS click [here](https://my.home-assistant.io/redirect/hacs_repository/?owner=amitfin&repository=lovelace-daily-schedule-card&category=plugin)._

Below are video clips demoing  Daily Schedule usage:
- [Create and modify](https://youtu.be/3cVtPPC3S4U)
- [Automation rule](https://youtu.be/5toly_W7fUU)

_Note: The built-in [Schedule integration](https://www.home-assistant.io/integrations/schedule/) should be used when a weekly schedule is needed._

## Create Daily Schedule

Use this link:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=daily_schedule)

Or, in the Home Assistant UI go through the following path:

[![Open your Home Assistant instance and show your settings menu.](https://my.home-assistant.io/badges/config.svg)](https://my.home-assistant.io/redirect/config/)

[![Open your Home Assistant instance and show your devices.](https://my.home-assistant.io/badges/devices.svg)](https://my.home-assistant.io/redirect/devices/)

[![Open your Home Assistant instance and show your helper entities.](https://my.home-assistant.io/badges/helpers.svg)](https://my.home-assistant.io/redirect/helpers/)

=> Click "+ Create helper" button and search for "Daily Schedule".

Here are screenshots from the new Daily Schedule flow:

![New Daily Schedule Name](https://raw.githubusercontent.com/amitfin/daily_schedule/master/screenshots/new1.png)![New Daily Schedule Time Range](https://raw.githubusercontent.com/amitfin/daily_schedule/master/screenshots/new2.png)

## Modify Daily Schedule

In the Home Assistant UI go through the following path:

[![Open your Home Assistant instance and show your settings menu.](https://my.home-assistant.io/badges/config.svg)](https://my.home-assistant.io/redirect/config/)

[![Open your Home Assistant instance and show your devices.](https://my.home-assistant.io/badges/devices.svg)](https://my.home-assistant.io/redirect/devices/)

[![Open your Home Assistant instance and show your helper entities.](https://my.home-assistant.io/badges/helpers.svg)](https://my.home-assistant.io/redirect/helpers/)

=> Find and click the entry on the list

=> Click the "Daily Schedule Options"

Follow the UI flow to add or remove time ranges:
1) Uncheck a time range to remove it.
2) Check the "Add a new time range" for adding a new time range.
3) It's not possible to edit a time range. Instead, remove the existing one and add a new one, which can be done in a single step.

Here are screenshots from the Daily Schedule options flow:

![Edit Daily Schedule Dialog](https://raw.githubusercontent.com/amitfin/daily_schedule/master/screenshots/edit1.png)![Edit Daily Schedule Time Range](https://raw.githubusercontent.com/amitfin/daily_schedule/master/screenshots/edit2.png)

Note: modifying Daily Schedule causes the binary sensor state to become ```unavailable``` momentarily. It's a side effect of the old binary sensor getting unloaded, just before the new binary sensor is created. This side effect might impact Automation Rules. Two ways to mitigate it can be:
  1) The rule should be triggered by explicit state values, e.g. by using the ```to: ["on", "off"]``` property in the state's trigger
  2) The rule should have the right mode, e.g. ```mode: restart```

## Schedule Validation

The schedule can be saved only if it passes the following checks:
1. Any time range length must be positive (not zero or negative).
2. Time ranges can’t overlap but can adjust.
3. The TO of the latest time range (in the day) can be smaller or equal to its FROM, and it will be treated as a time in the following day.
    - This means that the binary sensor will be always ON when there is a single time range with the same FROM and TO.

## Sun-based Schedule

It is not possible to directly set a time range using sun-based times, such as sunrise or sunset. However, below is a daily automation rule that demonstrates how it can be achieved:
```
- trigger:
    - platform: time
      at: "01:23"
  action:
    - variables:
        sunset_minus_30: >-
          {{ ((states('sensor.sun_next_setting') | as_datetime ) - timedelta(minutes=30))
          | as_timestamp | timestamp_custom('%H:%M:%S') }}
    - service: daily_schedule.set
      data:
        entity_id: binary_sensor.front_yard_lights
        schedule:
          - from: "{{ sunset_minus_30 }}"
            to: "00:00:00"
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

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)
