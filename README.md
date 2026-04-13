# Daily Schedule

[![HACS Badge](https://img.shields.io/badge/HACS-Default-31A9F4.svg?style=for-the-badge)](https://github.com/hacs/integration)

[![GitHub Release](https://img.shields.io/github/release/amitfin/daily_schedule.svg?style=for-the-badge&color=blue)](https://github.com/amitfin/daily_schedule/releases) ![Analytics](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=blue&label=Analytics&suffix=%20Installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.daily_schedule.total)

![Project Maintenance](https://img.shields.io/badge/maintainer-Amit%20Finkelstein-blue.svg?style=for-the-badge)

The Daily Schedule integration provides a binary sensor that gets its `on` / `off` state according to the user-defined schedule of time ranges.

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

This creates a `binary_sensor.<name>` entity with no time ranges configured yet. Use the Daily Schedule card to add the desired time ranges.

## Daily Schedule Card

### Install

You can add the Daily Schedule custom card to any dashboard by selecting "+ Add Card" in the built-in dashboard editor.

### Usage

Use the card to view and set Daily Schedule time ranges:

<img width="601" alt="image" src="https://github.com/user-attachments/assets/44dee96b-72e3-4bbe-81d4-b88c3ce9cb63" />
<br>
<img width="342" src="https://github.com/user-attachments/assets/3aa2fbc2-f8eb-4395-80c1-f73ca07a4812" />
<br>
<img src="https://github.com/user-attachments/assets/7466f370-f22c-49dc-888a-35233d55f065" width="534"/>

## Time Ranges

Each range has `from` and `to`. If the `to` is less than or equal `from` it's treated as time in the following day. One interesting case is when `from` equals `to`. This type of range covers the whole day (always on).

There are 3 ways to specify time:
1. An absolute time (e.g. 12:30).
2. Sunset with an optional negative or positive minutes offset.
3. Sunrise with an optional negative or positive minutes offset.

## Lovelace Card Configuration

### Visual Editor

| <img width="500" src="https://github.com/user-attachments/assets/aaf27761-4e3a-4afb-a5ed-b0b19f56eb92" /> |
|---|

### Code Editor

#### General

| Name     | Type   | Required | Default                       | Description                                                         |
| -------- | ------ | -------- | ----------------------------- | ------------------------------------------------------------------- |
| type     | string | True     | -                             | Must be `custom:daily-schedule-card`                                |
| title    | string | False    | -                             | Title of the card                                                   |
| card     | bool   | False    | _True if `title` is supplied_ | Whether to render an entire card or rows inside the `entities` card |
| template | string | False    | `Null`                        | Template for rendering the value. Has access to `entity_id`         |

#### Entities

| Name     | Type   | Required | Default                       | Description                                     |
| -------- | ------ | -------- | ----------------------------- | ----------------------------------------------- |
| entity   | string | True     | -                             | The `binary_sensor` entity ID                   |
| name     | string | False    | _Friendly name of the entity_ | Name to display                                 |
| template | string | False    | `Null`                        | Per-entity template (overrides card's template) |

_Note: the plain entity ID string can be specified (with no `entity:`) if there is no need to use other attributes._

#### Entities Card Example

```yaml
type: entities
entities:
  - type: custom:daily-schedule-card
    entities:
      - entity: binary_sensor.venta_schedule
        name: Venta
```

#### Entire Card Example

```yaml
type: custom:daily-schedule-card
title: Timers
entities:
  - binary_sensor.swimming_pool_filter_schedule
```

#### Template Example

```yaml
type: custom:daily-schedule-card
card: true
template: >-
  {{ state_attr(entity_id, 'effective_schedule') |
  map(attribute='from') | map('truncate', 2, True, '')
  | join(' | ') }}
entities:
  - binary_sensor.let_the_dog_out
```

## Attributes

The binary sensor has the following attributes:
1. `Schedule`: the list of `on` time ranges as provided by the user.
2. `Effective schedule`: the actual `on` time ranges: (1) disabled ranges are ignored, (2) dynamic times (sunrise / sunset) are resolved to absolute time (changing daily), (3) the user-provided ranges are merged and duplications are removed, i.e. the list doesn't have overlapping or adjusting ranges.
3. `Next toggle`: the next time when the binary sensor is going to change its state.
4. `Next toggles`: a list with the 4 next times when the binary sensor is going to change its state. The 1st element is identical to `Next toggle`.

## Daylight Saving Time Handling

When the local timezone transitions for daylight saving time (DST), the logic handles edge cases explicitly:
1. **Forward gaps (non-existent times)**<br>
   When DST starts, the clock jumps forward and certain local times do not exist (for example, from `01:59` directly to `03:00`). If a scheduled toggle falls within this missing interval, it is advanced to the next valid local time. For example, if the schedule defines a toggle at `02:30`, it will be adjusted to `03:00`. Note that ranges overlapping the forward gap will run for a shorter duration than intended on the day DST begins.
2. **Fall-back ambiguity (repeated local times)**<br>
   When DST ends, the clock moves backward and a local hour repeats (for example, `01:00–01:59` occurs twice). In this case, toggles within the repeated interval may occur twice, distinguished by their [fold](https://docs.python.org/3/library/datetime.html#datetime.datetime.fold) value. For example, if the schedule contains a single range `00:30–01:30` and the current time is `00:00`, the next four toggles will be:

      1. `00:30` (`on`, `fold=0`)
	  2. `01:30` (`off`, `fold=0`)
	  3. `01:00` (`on`, `fold=1`) — the clock has moved backward. Note that `01:00` is never a toggle, except here.
	  4. `01:30` (`off`, `fold=1`)

    Ranges overlapping the repeated interval will therefore run longer than intended on the day DST ends.

## `set` Action

`daily_schedule.set` action can be used to configure the time ranges. Here is an example:

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

Notes:
1. It's uncommon to perform this action directly. Its main usage is indirectly via the [Lovelace card](https://github.com/amitfin/lovelace-daily-schedule-card).
2. There is no corresponding `get`. The data already exists as attributes:

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
This is an advanced option that should not be used in the majority of the use cases. It should be used only if there is a very concrete reason to do so. This option should not be used when sunrise or sunset are used since they are resolved by using the local time zone.

## Skip-Reversed Option

When enabled (disabled by default), this option ignores any time range with sunrise or sunset where the `to` time is earlier than or equal to the `from` time. This behavior is dynamic. For example, a range defined as sunrise → 7:00 AM may become reversed during parts of the year if sunrise occurs after 7:00 AM. In such cases, the range is applied only when sunrise is earlier than 7:00 AM, and automatically skipped when sunrise is at 7:00 AM or later.
A time range with absolute `from` and `to` times is never skipped, even if it's reversed and this option is enabled. Such a time range should be deleted or disabled manually if it's not needed.

## Removing the Integration

1. **Delete the configuration:**
   - Open the integration page ([my-link](https://my.home-assistant.io/redirect/integration/?domain=daily_schedule)). Delete all helper entities by clicking the 3‑dot menu (⋮), and selecting **Delete**.

2. **Remove the integration files:**
   - If the integration was installed via **HACS**, follow the [official HACS removal instructions](https://www.hacs.xyz/docs/use/repositories/dashboard/#removing-a-repository).
   - Otherwise, manually delete the integration’s folder `custom_components/daily_schedule`.

📌 A **Home Assistant core restart** is required to fully apply the removal.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)



