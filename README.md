# Daily Schedule

[![GitHub Release][releases-shield]][releases]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

The Daily Schedule integration provides a binary sensor that gets its ON/OFF state according to the user-defined schedule.
A schedule is a list of time ranges, defined by FROM and TO times.

## Schedule Validation
1. Time ranges’ lengths should be positive (not zero or negative).
2. Time ranges can’t overlap but can adjust.
3. The TO time of the latest time range can be smaller or equal to the FROM time, and it will be treated as a time in the following day.
    - For example, the binary sensor will always be in ON state when there is a single time range with the same FROM and TO times.

## Configuration is done in the UI

In the Home Assistant UI go to [Settings](https://my.home-assistant.io/redirect/config) -> [Devices & Services](https://my.home-assistant.io/redirect/integrations) -> [Helpers](https://my.home-assistant.io/redirect/helpers) -> click [Create helper](https://my.home-assistant.io/redirect/config_flow_start?domain=daily_schedule) and search for "Daily Schedule".

Here is a direct link via "My Home Assistant":

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=daily_schedule)

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

<!---->

***

[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/amitfin/daily_schedule.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Amit%20Finkelstein%20%40amitfin-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/amitfin/daily_schedule.svg?style=for-the-badge
[releases]: https://github.com/amitfin/daily_schedule/releases
