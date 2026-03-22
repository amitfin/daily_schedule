class DailyScheduleCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._config) {
      return;
    }
    if (!this._dialog) {
      this._getInputTimeWidth();
      this._createDialog();
      this.appendChild(this._dialog);
    } else {
      this._dialog.hass = hass;
    }
    if (!this._content) {
      this._content = this._createContent();
      if (this._config.title || this._config.card) {
        const card = document.createElement("ha-card");
        card.header = this._config.title;
        this._content.classList.add("card-content");
        card.appendChild(this._content);
        this.appendChild(card);
      } else {
        this.appendChild(this._content);
      }
    } else {
      this._updateContent();
    }
  }

  setConfig(config) {
    if (
      this._config !== null &&
      JSON.stringify(this._config) === JSON.stringify(config)
    ) {
      this._config = config;
      return;
    }
    if (!config.entities) {
      throw new Error("You need to define entities");
    }
    this._config = config;
    this.innerHTML = "";
    this._content = null;
    this._dialog = null;
  }

  getCardSize() {
    return this._config ? this._config.entities.length : 1;
  }

  static getConfigForm() {
    return {
      schema: [
        {
          name: "title",
          selector: { text: {} },
        },
        {
          name: "entities",
          required: true,
          selector: {
            entity: {
              multiple: true,
              reorder: true,
              filter: {
                domain: "binary_sensor",
                integration: "daily_schedule",
              },
            },
          },
        },
      ],
      assertConfig: (config) => {
        if (Array.isArray(config?.entities)) {
          for (const entry of config.entities) {
            if (typeof entry !== "string") {
              throw new Error(
                "Visual editor is not available for entity options.",
              );
            }
          }
        }
      },
      computeLabel: (schema, localize) => {
        switch (schema.name) {
          case "title":
            return `${localize("ui.panel.lovelace.editor.card.generic.title")} (${localize(
              "ui.panel.lovelace.editor.card.config.optional",
            )})`;
          case "entities":
            return `${localize("ui.panel.lovelace.editor.card.generic.entities")} (${localize(
              "ui.panel.lovelace.editor.card.config.required",
            )})`;
          default:
            return schema.name;
        }
      },
    };
  }

  static getStubConfig() {
    return { card: true, entities: [] };
  }

  _createContent() {
    const content = document.createElement("DIV");
    content._rows = [];
    for (const entry of this._config.entities) {
      const entity = entry.entity || entry;
      const row = document.createElement("DIV");
      row._entity = entity;
      row._template_value = entry.template || this._config.template;
      row.classList.add("card-content");
      if (this._hass.states[entity]) {
        const rowContent = this._createCardRow(
          entity,
          entry.name ||
            this._hass.states[entity].attributes.friendly_name ||
            entity,
        );
        row._content = rowContent;
        this._setCardRowValue(row);
        row.appendChild(rowContent);
        content._rows.push(row);
      } else {
        row.innerText = `Entity not found: ${entity}`;
      }
      content.appendChild(row);
    }
    return content;
  }

  _updateContent() {
    for (const row of this._content._rows) {
      row._content._icon.hass = this._hass;
      row._content._icon.stateObj = this._hass.states[row._entity];
      this._setCardRowValue(row);
    }
  }

  _createCardRow(entity, name) {
    const content = document.createElement("DIV");
    content.style.cursor = "pointer";
    content.style.display = "flex";
    content.style.alignItems = "center";
    content.style.gap = "16px";
    const icon = document.createElement("state-badge");
    icon.style.flex = "none";
    icon.hass = this._hass;
    icon.stateObj = this._hass.states[entity];
    icon.stateColor = true;
    content._icon = icon;
    content.appendChild(icon);
    const name_element = document.createElement("P");
    name_element.innerText = name;
    content.appendChild(name_element);
    const value_element = document.createElement("P");
    value_element.style.marginInlineStart = "auto";
    value_element.style.textAlign = "end";
    content._value_element = value_element;
    content.appendChild(value_element);
    content.onclick = () => {
      this._dialog._entity = entity;
      this._dialog.headerTitle = name;
      this._dialog._message.innerText = "";
      this._dialog._schedule = [...this._getStateSchedule(entity)];
      this._createDialogRows();
      this._dialog.open = true;
    };
    return content;
  }

  _getStateSchedule(entity, effective = false) {
    const state = this._hass.states[entity];
    return !state
      ? []
      : !effective
        ? state.attributes.schedule || []
        : state.attributes.effective_schedule || [];
  }

  _rowEntityChanged(row) {
    const entity_data = this._hass.states[row._entity]
      ? JSON.stringify(
          (({ state, attributes }) => ({ state, attributes }))(
            this._hass.states[row._entity],
          ),
        )
      : null;
    const changed = row._entity_data !== entity_data;
    row._entity_data = entity_data;
    return changed;
  }

  _rowTemplateValue(row) {
    const subscribed = this._hass.connection.subscribeMessage(
      (message) => {
        row._content._value_element.innerHTML = message.result.length
          ? `<bdi dir="ltr">${message.result}</bdi>`
          : "&empty;";
        subscribed.then((unsub) => unsub());
      },
      {
        type: "render_template",
        template: row._template_value,
        variables: { entity_id: row._entity },
      },
    );
  }

  _setCardRowValue(row) {
    if (!this._rowEntityChanged(row)) {
      return;
    }
    if (!row._template_value) {
      const schedule = this._getStateSchedule(row._entity, true);
      if (!schedule.length) {
        row._content._value_element.innerHTML = "&empty;";
      } else if (schedule.length === 1 && schedule[0].from === schedule[0].to) {
        row._content._value_element.innerHTML = "&infin;";
      } else {
        const ranges = schedule
          .map((range) => `${range.from.slice(0, -3)}-${range.to.slice(0, -3)}`)
          .join(", ");
        row._content._value_element.innerHTML = `<bdi dir="ltr">${ranges}</bdi>`;
      }
    } else {
      this._rowTemplateValue(row);
    }
  }

  _createDialog() {
    if (!this._isMobileView()) {
      this._dialog = document.createElement("ha-dialog");
    } else {
      this._dialog = document.createElement("ha-adaptive-dialog");
      this._dialog.setAttribute("flexcontent", "");
      this._dialog.style.setProperty(
        "--ha-bottom-sheet-height",
        "calc(100dvh - max(var(--safe-area-inset-top), 48px))",
      );
      this._dialog.style.setProperty(
        "--ha-bottom-sheet-max-height",
        "var(--ha-bottom-sheet-height)",
      );
    }
    this._dialog.hass = this._hass;
    this._dialog.setAttribute("dir", "ltr");
    this._dialog.addEventListener("closed", () => {
      this._dialog.open = false;
    });
    this._createDialogHeader();
    this._dialog.open = false;
    const scroller = document.createElement("div");
    Object.assign(scroller.style, {
      display: "inline-block",
      width: "max-content",
      maxWidth: "none",
      whiteSpace: "nowrap",
      boxSizing: "border-box",
    });
    this._dialog._scroller = scroller;
    this._dialog.appendChild(scroller);
    const plus = document.createElement("ha-icon-button");
    plus.style.marginLeft = "-12px";
    const icon = document.createElement("ha-icon");
    icon.icon = "mdi:plus";
    plus.appendChild(icon);
    plus.onclick = () => {
      this._dialog._schedule.push({ from: null, to: null });
      this._createDialogRows();
      this._saveBackendEntity();
    };
    this._dialog._plus = plus;
    const message = document.createElement("P");
    message.style.display = "flex";
    message.style.color = "red";
    message.innerText = "";
    this._dialog._message = message;
  }

  _isMobileView() {
    return window.matchMedia("(max-width: 600px)").matches;
  }

  _createDialogRows() {
    this._dialog._scroller.innerHTML = "";
    for (const [index, range] of this._dialog._schedule.entries()) {
      this._dialog._scroller.appendChild(this._createDialogRow(range, index));
    }
    this._dialog._scroller.appendChild(this._dialog._plus);
    this._dialog._scroller.appendChild(this._dialog._message);
  }

  _createDialogHeader() {
    const header = document.createElement("DIV");
    header.slot = "headerNavigationIcon";
    header.style.display = "flex";
    header.style.alignItems = "center";

    const close = document.createElement("ha-icon-button");
    close.dataset.role = "dialog-close";
    const close_icon = document.createElement("ha-icon");
    close_icon.icon = "mdi:close";
    close.appendChild(close_icon);
    close.onclick = () => {
      this._dialog.open = false;
    };
    header.appendChild(close);

    const more_info = document.createElement("ha-icon-button");
    more_info.slot = "headerActionItems";
    more_info.dataset.role = "more-info";
    const more_info_icon = document.createElement("ha-icon");
    more_info_icon.icon = "mdi:information-outline";
    more_info.appendChild(more_info_icon);
    more_info.onclick = () => {
      this._dialog.open = false;
      const event = new Event("hass-more-info", {
        bubbles: true,
        cancelable: false,
        composed: true,
      });
      event.detail = { entityId: this._dialog._entity };
      this.dispatchEvent(event);
    };
    this._dialog.appendChild(more_info);
    this._dialog.appendChild(header);
  }

  _createDialogRow(range, index) {
    const row = document.createElement("DIV");
    row.style.color = getComputedStyle(document.body).getPropertyValue("color");
    row.style.display = "flex";
    row.style.gap = "4px";
    row.style.alignItems = "center";
    row.style.marginTop = "12px";

    this._createTimeInput(range, "from", row);

    const arrow = document.createElement("ha-icon");
    arrow.icon = "mdi:arrow-right-thick";
    row.appendChild(arrow);

    this._createTimeInput(range, "to", row);

    const toggle = document.createElement("ha-switch");
    toggle.style.marginLeft = "auto";
    toggle.style.paddingLeft = "16px";
    toggle.checked = !range.disabled;
    toggle.addEventListener("change", () => {
      range.disabled = !range.disabled;
      this._saveBackendEntity();
    });
    row.appendChild(toggle);

    const remove = document.createElement("ha-icon");
    remove.icon = "mdi:delete-outline";
    remove.style.cursor = "pointer";
    remove.onclick = () => {
      this._dialog._schedule = this._dialog._schedule.filter(
        (_, i) => i !== index,
      );
      this._createDialogRows();
      this._saveBackendEntity();
    };
    row.appendChild(remove);

    return row;
  }

  _createTimeInput(range, type, row) {
    const sunrise = "↑";
    const sunset = "↓";
    const time_input = document.createElement("INPUT");
    const type_symbol = document.createElement("ha-icon");

    if (
      range[type] &&
      (range[type][0] === sunrise || range[type][0] === sunset)
    ) {
      this._setInputType(
        range[type][0] === sunrise ? "sunrise" : "sunset",
        type_symbol,
        time_input,
        range[type].slice(1),
      );
    } else {
      this._setInputType("time", type_symbol, time_input, range[type]);
    }

    type_symbol.style.cursor = "pointer";
    type_symbol.onclick = () => {
      if (type_symbol._type === "time") {
        this._setInputType("sunrise", type_symbol, time_input, null);
      } else if (type_symbol._type === "sunrise") {
        this._setInputType("sunset", type_symbol, time_input, null);
      } else {
        this._setInputType("time", type_symbol, time_input, null);
      }
      time_input.onchange();
    };

    Object.assign(time_input.style, {
      width: `${this._input_time_width}px`,
      minWidth: `${this._input_time_width}px`,
      boxSizing: "border-box",
      padding: "4px 0",
      cursor: "pointer",
    });

    time_input.onchange = () => {
      if (!time_input.value) {
        range[type] = null;
        this._saveBackendEntity();
        return;
      }
      let value;
      if (type_symbol._type === "time") {
        value = `${time_input.value}:00`;
      } else {
        value = type_symbol._type === "sunrise" ? sunrise : sunset;
        if (time_input.value) {
          const value_int = parseInt(time_input.value, 10);
          if (value_int) {
            value += `${value_int > 0 ? "+" : ""}${time_input.value}`;
          }
        }
      }
      if (range[type] !== value) {
        range[type] = value;
        this._saveBackendEntity();
      }
    };

    row.appendChild(type_symbol);
    row.appendChild(time_input);
  }

  _setInputType(type, symbol, input, value) {
    symbol._type = type;
    if (type === "sunrise" || type === "sunset") {
      input.type = "number";
      input.value = parseInt(value || "0", 10);
      symbol.icon =
        type === "sunrise" ? "mdi:weather-sunny" : "mdi:weather-night";
    } else {
      input.type = "time";
      if (value) {
        const time = value.split(":");
        input.value = `${time[0]}:${time[1]}`;
      } else if (input.value) {
        input.value = null;
      }
      symbol.icon = "mdi:clock-outline";
    }
  }

  _getInputTimeWidth() {
    if (!this._input_time_width) {
      const dummyInput = document.createElement("INPUT");
      dummyInput.type = "time";
      dummyInput.style.visibility = "hidden";
      this.appendChild(dummyInput);
      setTimeout(() => {
        this._input_time_width = Math.min(
          dummyInput.getBoundingClientRect().width,
          100,
        );
        dummyInput.remove();
      }, 0);
    }
  }

  _saveBackendEntity() {
    const schedule = this._dialog._schedule || [];

    for (const range of schedule) {
      if (range.from === null || range.to === null) {
        if (this._dialog._message.innerText !== "Missing field(s).") {
          this._dialog._message.innerText = "Missing field(s).";
        }
        return;
      }
    }

    this._hass
      .callService("daily_schedule", "set", {
        entity_id: this._dialog._entity,
        schedule,
      })
      .then(() => {
        if (this._dialog._message.innerText.length > 0) {
          this._dialog._message.innerText = "";
        }
      })
      .catch((error) => {
        if (this._dialog._message.innerText !== error.message) {
          this._dialog._message.innerText = error.message;
        }
      });
  }
}

function _register(elementTag, className) {
  if (!customElements.get(elementTag)) {
    customElements.define(elementTag, className);
  }
}
_register("daily-schedule-card", DailyScheduleCard);
customElements
  .whenDefined("home-assistant")
  .then(() => _register("daily-schedule-card", DailyScheduleCard));
window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "daily-schedule-card")) {
  window.customCards.push({
    type: "daily-schedule-card",
    name: "Daily Schedule",
    description: "Card for displaying and editing Daily Schedule entities.",
    documentationURL: "https://github.com/amitfin/lovelace-daily-schedule-card",
  });
}
