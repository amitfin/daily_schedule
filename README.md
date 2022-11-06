# Daily Schedule

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

The Daily Schedule integration provides a binary sensor that gets its ON/OFF state according to the user-defined schedule.

_Note: There is an optional [lovelace card](https://github.com/amitfin/lovelace-daily-schedule-card) with an optimized view and simplyfied editing capabilities. It doesn't add functionality, but it improves the user experience._

Below are video clips demoing  Daily Schedule usage:
- [Create and modify](https://youtu.be/3cVtPPC3S4U)
- [Automation rule](https://youtu.be/5toly_W7fUU)

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
3) It's not possible to edit a time range. Instead, remove the exsiting one and add a new one, which can be done in a single step.

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

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

<!---->

***

[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/amitfin/daily_schedule.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Amit%20Finkelstein%20%40amitfin-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/amitfin/daily_schedule.svg?style=for-the-badge
[releases]: https://github.com/amitfin/daily_schedule/releases

