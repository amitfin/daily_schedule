import {
  afterEach,
  beforeAll,
  beforeEach,
  describe,
  expect,
  test,
  vi,
} from "vitest";

/**
 * Test harness notes:
 * - We stub HA web components used by the card/editor.
 * - We simulate HA "hass" object shape minimally (states, entities, localize, callService, connection.subscribeMessage).
 */

beforeAll(() => {
  // ha-card
  if (!customElements.get("ha-card")) {
    class HaCard extends HTMLElement {
      set header(v) {
        this._header = v;
      }
      get header() {
        return this._header;
      }
    }
    customElements.define("ha-card", HaCard);
  }

  // ha-dialog
  if (!customElements.get("ha-dialog")) {
    class HaDialog extends HTMLElement {
      constructor() {
        super();
        this.open = false;
        this.width = "medium";
        this.headerTitle = undefined;
      }
    }
    customElements.define("ha-dialog", HaDialog);
  }

  // ha-adaptive-dialog
  if (!customElements.get("ha-adaptive-dialog")) {
    class HaAdaptiveDialog extends HTMLElement {
      constructor() {
        super();
        this.open = false;
        this.width = "medium";
        this.headerTitle = undefined;
      }
    }
    customElements.define("ha-adaptive-dialog", HaAdaptiveDialog);
  }

  // state-badge
  if (!customElements.get("state-badge")) {
    class StateBadge extends HTMLElement {
      set hass(v) {
        this._hass = v;
      }
      get hass() {
        return this._hass;
      }
      set stateObj(v) {
        this._stateObj = v;
      }
      get stateObj() {
        return this._stateObj;
      }
      set stateColor(v) {
        this._stateColor = v;
      }
      get stateColor() {
        return this._stateColor;
      }
    }
    customElements.define("state-badge", StateBadge);
  }

  // ha-icon
  if (!customElements.get("ha-icon")) {
    class HaIcon extends HTMLElement {
      set icon(v) {
        this._icon = v;
      }
      get icon() {
        return this._icon;
      }
    }
    customElements.define("ha-icon", HaIcon);
  }

  // mwc-icon-button
  if (!customElements.get("mwc-icon-button")) {
    class MwcIconButton extends HTMLElement {
      constructor() {
        super();
        this.disabled = false;
      }
    }
    customElements.define("mwc-icon-button", MwcIconButton);
  }

  // ha-switch
  if (!customElements.get("ha-switch")) {
    class HaSwitch extends HTMLElement {
      constructor() {
        super();
        this.checked = false;
      }
    }
    customElements.define("ha-switch", HaSwitch);
  }

  // ha-textfield
  if (!customElements.get("ha-textfield")) {
    class HaTextfield extends HTMLElement {
      constructor() {
        super();
        this.value = "";
        this.label = "";
      }
    }
    customElements.define("ha-textfield", HaTextfield);
  }

  // ha-entity-picker
  if (!customElements.get("ha-entity-picker")) {
    class HaEntityPicker extends HTMLElement {
      constructor() {
        super();
        this.value = "";
        this.index = undefined;
        this.hass = undefined;
        this.includeDomains = undefined;
        this.entityFilter = undefined;
      }

      emitValue(value) {
        const ev = new Event("value-changed");
        ev.detail = { value };
        this.dispatchEvent(ev);
      }
    }
    customElements.define("ha-entity-picker", HaEntityPicker);
  }

  // ha-svg-icon
  if (!customElements.get("ha-svg-icon")) {
    class HaSvgIcon extends HTMLElement {
      set path(v) {
        this._path = v;
      }
      get path() {
        return this._path;
      }
    }
    customElements.define("ha-svg-icon", HaSvgIcon);
  }

  // ha-sortable
  if (!customElements.get("ha-sortable")) {
    class HaSortable extends HTMLElement {
      constructor() {
        super();
        this.handleSelector = "";
      }

      emitMoved(oldIndex, newIndex) {
        const ev = new Event("item-moved");
        ev.detail = { oldIndex, newIndex };
        this.dispatchEvent(ev);
      }
    }
    customElements.define("ha-sortable", HaSortable);
  }

  // hui-entities-card (editor workaround)
  if (!customElements.get("hui-entities-card")) {
    class HuiEntitiesCard extends HTMLElement {
      static getConfigElement() {
        return document.createElement("div");
      }
    }
    customElements.define("hui-entities-card", HuiEntitiesCard);
  }
});

// Import registers card + editor from product file
import "../custom_components/daily_schedule/card/daily-schedule-card.js";

function createHass({
  states = {},
  entities = {},
  callServiceImpl,
  subscribeMessageImpl,
} = {}) {
  const unsub = vi.fn();

  const subscribeMessage =
    subscribeMessageImpl ||
    vi.fn((cb, payload) => {
      subscribeMessage._last = { cb, payload };
      return Promise.resolve(unsub);
    });

  const callService =
    callServiceImpl ||
    vi.fn(() => {
      return Promise.resolve();
    });

  const localize = vi.fn((key) => key);

  return {
    states,
    entities,
    localize,
    callService,
    connection: {
      subscribeMessage,
    },
  };
}

function mountCard(config, hass) {
  const el = document.createElement("daily-schedule-card");
  document.body.appendChild(el);
  if (config) el.setConfig(config);
  if (hass) el.hass = hass;
  return el;
}

function flushMicrotasks(times = 2) {
  let p = Promise.resolve();
  for (let i = 0; i < times; i++) p = p.then(() => {});
  return p;
}

beforeEach(() => {
  document.body.style.color = "rgb(0, 0, 0)";
  window.matchMedia = vi.fn((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
});

afterEach(() => {
  document.body.innerHTML = "";
  vi.useRealTimers();
});

describe("DailyScheduleCard - registration & basic API", () => {
  test("custom elements are registered", () => {
    expect(customElements.get("daily-schedule-card")).toBeDefined();
  });

  test("delayed registration path resolves after home-assistant is defined", async () => {
    if (!customElements.get("home-assistant")) {
      customElements.define("home-assistant", class extends HTMLElement {});
    }

    await flushMicrotasks();

    expect(customElements.get("daily-schedule-card")).toBeDefined();
  });

  test("window.customCards is populated", () => {
    expect(Array.isArray(window.customCards)).toBe(true);
    const entry = window.customCards.find(
      (c) => c.type === "daily-schedule-card",
    );
    expect(entry).toBeDefined();
    expect(entry.name).toBeTruthy();
    expect(entry.description).toBeTruthy();
    expect(entry.documentationURL).toMatch(/github/i);
  });

  test("window.customCards does not add a duplicate entry on repeated module evaluation", async () => {
    const originalCustomCards = window.customCards;
    window.customCards = [
      {
        type: "different-card",
        name: "Different Card",
        description: "another entry",
        documentationURL: "https://example.com/different",
      },
      {
        type: "daily-schedule-card",
        name: "Existing Daily Schedule",
        description: "existing entry",
        documentationURL: "https://example.com/existing",
      },
    ];

    try {
      vi.resetModules();
      await import(
        "../custom_components/daily_schedule/card/daily-schedule-card.js"
      );
    } finally {
      const entries = window.customCards.filter(
        (card) => card.type === "daily-schedule-card",
      );
      expect(entries).toHaveLength(1);
      expect(entries[0].name).toBe("Existing Daily Schedule");
      window.customCards = originalCustomCards;
    }
  });

  test("create element + getConfigForm + stub config", () => {
    const el = document.createElement("daily-schedule-card");
    expect(el).toBeInstanceOf(HTMLElement);

    const configForm = customElements
      .get("daily-schedule-card")
      .getConfigForm();
    expect(configForm).toBeTruthy();
    expect(configForm.schema).toBeInstanceOf(Array);

    const stub = customElements.get("daily-schedule-card").getStubConfig();
    expect(stub).toEqual({ card: true, entities: [] });
  });

  test("setConfig throws when entities missing", () => {
    const el = document.createElement("daily-schedule-card");
    expect(() => el.setConfig({})).toThrow(/define entities/i);
  });

  test("getCardSize returns length or 1 when no config", () => {
    const el = document.createElement("daily-schedule-card");
    expect(el.getCardSize()).toBe(1);

    el.setConfig({ entities: ["sensor.a", "sensor.b"] });
    expect(el.getCardSize()).toBe(2);
  });

  test("hass setter returns early when no config", () => {
    const el = document.createElement("daily-schedule-card");
    const hass = createHass();
    el.hass = hass;
    expect(el._dialog).toBeUndefined();
    expect(el._content).toBeUndefined();
  });

  test("setConfig same config path (no rerender) executes", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: { friendly_name: "A", effective_schedule: [] },
        },
      },
    });
    const el = mountCard({ entities: ["sensor.a"] }, hass);

    const beforeContent = el._content;
    el.setConfig({ entities: ["sensor.a"] });
    expect(el._content).toBe(beforeContent);
  });
});

describe("DailyScheduleCard - content creation, update, schedules & template", () => {
  test("renders with card wrapper when title or card flag is set", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: { friendly_name: "A", effective_schedule: [] },
        },
      },
    });

    const el1 = mountCard({ entities: ["sensor.a"], title: "MyTitle" }, hass);
    expect(el1.querySelector("ha-card")).toBeTruthy();

    const el2 = mountCard({ entities: ["sensor.a"], card: true }, hass);
    expect(el2.querySelector("ha-card")).toBeTruthy();
  });

  test("renders without card wrapper when no title and no card flag", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: { friendly_name: "A", effective_schedule: [] },
        },
      },
    });
    const el = mountCard({ entities: ["sensor.a"] }, hass);
    expect(el.querySelector("ha-card")).toBeFalsy();
    expect(el._content).toBeDefined();
    expect(el._content._rows).toHaveLength(1);
  });

  test("shows 'Entity not found' when entity missing (object entry path)", () => {
    const hass = createHass({
      states: {
        "sensor.exists": {
          state: "on",
          attributes: { friendly_name: "OK", effective_schedule: [] },
        },
      },
    });

    const card = mountCard(
      { entities: [{ entity: "sensor.missing", name: "Missing" }] },
      hass,
    );
    const row = card._content.children[0];

    expect(card._content._rows).toHaveLength(0);
    expect(row.innerText).toMatch(/Entity not found/i);
    expect(row.innerText).toMatch(/sensor\.missing/i);
  });

  test("row uses name override, else friendly_name, else entity", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: { friendly_name: "Friendly", effective_schedule: [] },
        },
        "sensor.b": { state: "on", attributes: { effective_schedule: [] } },
      },
    });

    const card = mountCard(
      {
        entities: [
          { entity: "sensor.a", name: "Override" },
          "sensor.a",
          "sensor.b",
        ],
      },
      hass,
    );

    const [r0, r1, r2] = card._content._rows;

    expect(r0._content.querySelector("p")?.innerText).toBe("Override");
    expect(r1._content.querySelector("p")?.innerText).toBe("Friendly");
    expect(r2._content.querySelector("p")?.innerText).toBe("sensor.b");
  });

  test("_getStateSchedule falls back to [] when schedule/effective_schedule missing", () => {
    const hass = createHass({
      states: {
        "binary_sensor.a": {
          state: "on",
          attributes: {}, // no schedule fields
        },
      },
    });
    const card = mountCard({ entities: ["binary_sensor.a"] }, hass);

    expect(card._getStateSchedule("binary_sensor.a")).toEqual([]);
    expect(card._getStateSchedule("binary_sensor.a", true)).toEqual([]);
  });

  test("_getStateSchedule returns correct schedule vs effective_schedule and empty when no state", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            schedule: [{ from: "01:00:00", to: "02:00:00" }],
            effective_schedule: [{ from: "03:00:00", to: "04:00:00" }],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);

    expect(card._getStateSchedule("sensor.a", false)).toEqual([
      { from: "01:00:00", to: "02:00:00" },
    ]);
    expect(card._getStateSchedule("sensor.a", true)).toEqual([
      { from: "03:00:00", to: "04:00:00" },
    ]);
    expect(card._getStateSchedule("sensor.missing", true)).toEqual([]);
  });

  test("_rowEntityChanged detects changes (including missing state)", () => {
    const hass = createHass({
      states: {
        "sensor.a": { state: "on", attributes: { x: 1 } },
      },
    });
    const card = mountCard({ entities: ["sensor.a"] }, hass);

    const row = { _entity: "sensor.a", _entity_data: undefined };
    expect(card._rowEntityChanged(row)).toBe(true);
    expect(card._rowEntityChanged(row)).toBe(false);

    card._hass.states["sensor.a"] = { state: "off", attributes: { x: 1 } };
    expect(card._rowEntityChanged(row)).toBe(true);

    row._entity = "sensor.missing";
    expect(card._rowEntityChanged(row)).toBe(true);
    expect(card._rowEntityChanged(row)).toBe(false);
  });

  test("_setCardRowValue returns early when entity data unchanged", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: { friendly_name: "A", effective_schedule: [] },
        },
      },
    });
    const card = mountCard({ entities: ["sensor.a"] }, hass);

    const row = card._content._rows[0];
    // Prime _entity_data to match current hass state
    card._rowEntityChanged(row);

    const spy = vi.spyOn(card, "_getStateSchedule");
    card._setCardRowValue(row);

    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  test("formats empty schedule as &empty; (becomes ∅)", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: { friendly_name: "A", effective_schedule: [] },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);
    const row = card._content._rows[0];
    expect(row._content._value_element.textContent).toBe("∅");
  });

  test("formats infinity schedule (from==to) as ∞", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            effective_schedule: [{ from: "00:00:00", to: "00:00:00" }],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);
    const row = card._content._rows[0];
    expect(row._content._value_element.textContent).toBe("∞");
  });

  test("formats multiple ranges list inside <bdi>", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            effective_schedule: [
              { from: "09:15:00", to: "10:45:00" },
              { from: "13:00:00", to: "14:30:00" },
            ],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);
    const row = card._content._rows[0];

    const bdi = row._content._value_element.querySelector("bdi");
    expect(bdi).toBeTruthy();
    expect(bdi.textContent).toContain("09:15-10:45");
    expect(bdi.textContent).toContain("13:00-14:30");
  });

  test("template path subscribes, updates value, and unsubscribes", async () => {
    const unsub = vi.fn();
    const subscribeMessage = vi.fn((cb, payload) => {
      subscribeMessage._last = { cb, payload };
      return Promise.resolve(unsub);
    });

    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: { friendly_name: "A", effective_schedule: [] },
        },
      },
      subscribeMessageImpl: subscribeMessage,
    });

    const template = "{{ states(entity_id) }}";
    const card = mountCard(
      { entities: [{ entity: "sensor.a", template }] },
      hass,
    );

    expect(hass.connection.subscribeMessage).toHaveBeenCalledTimes(1);

    const last = hass.connection.subscribeMessage._last;
    expect(last.payload).toMatchObject({
      type: "render_template",
      template,
      variables: { entity_id: "sensor.a" },
    });

    const row = card._content._rows[0];

    last.cb({ result: "hello" });
    await flushMicrotasks(2);

    expect(row._content._value_element.textContent).toContain("hello");
    expect(unsub).toHaveBeenCalledTimes(1);

    card._hass.states["sensor.a"] = {
      state: "off",
      attributes: { friendly_name: "A", effective_schedule: [] },
    };
    card._setCardRowValue(row);

    const last2 = hass.connection.subscribeMessage._last;
    last2.cb({ result: "" });
    await flushMicrotasks(2);

    expect(row._content._value_element.textContent).toBe("∅");
    expect(unsub).toHaveBeenCalledTimes(2);
  });

  test("_updateContent updates icon hass/stateObj and recomputes value", () => {
    const hass1 = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            effective_schedule: [{ from: "09:00:00", to: "10:00:00" }],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass1);
    const row = card._content._rows[0];

    expect(row._content._icon.hass).toBe(hass1);
    expect(row._content._icon.stateObj.state).toBe("on");
    expect(row._content._value_element.textContent).toContain("09:00-10:00");

    const hass2 = createHass({
      states: {
        "sensor.a": {
          state: "off",
          attributes: {
            friendly_name: "A",
            effective_schedule: [{ from: "11:00:00", to: "12:00:00" }],
          },
        },
      },
    });

    card.hass = hass2;

    expect(row._content._icon.hass).toBe(hass2);
    expect(row._content._icon.stateObj.state).toBe("off");
    expect(row._content._value_element.textContent).toContain("11:00-12:00");
  });
});

describe("DailyScheduleCard - dialog behavior (open, add, toggle, remove, close, more-info)", () => {
  test("dialog is created with desktop ha-dialog configuration", () => {
    const hass = createHass();
    const card = mountCard({ entities: ["binary_sensor.a"] }, hass);

    expect(card._dialog).toBeDefined();
    expect(card._dialog.tagName).toBe("HA-DIALOG");
    expect(card._dialog.width).toBe("medium");
  });

  test("dialog uses ha-adaptive-dialog on mobile", () => {
    window.matchMedia = vi.fn((query) => ({
      matches: query === "(max-width: 600px)",
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    const hass = createHass();
    const card = mountCard({ entities: ["binary_sensor.a"] }, hass);

    expect(card._dialog.tagName).toBe("HA-ADAPTIVE-DIALOG");
    expect(card._dialog.width).toBe("medium");
    expect(card._dialog.hasAttribute("flexcontent")).toBe(true);
    expect(
      card._dialog.style.getPropertyValue("--ha-bottom-sheet-height"),
    ).toBe("calc(100dvh - max(var(--safe-area-inset-top), 48px))");
    expect(
      card._dialog.style.getPropertyValue("--ha-bottom-sheet-max-height"),
    ).toBe("var(--ha-bottom-sheet-height)");
  });

  test("dialog closed event resets open flag", () => {
    const hass = createHass();
    const card = mountCard({ entities: ["binary_sensor.a"] }, hass);

    card._dialog.open = true;
    card._dialog.dispatchEvent(new Event("closed"));

    expect(card._dialog.open).toBe(false);
  });

  test("clicking row populates dialog and creates rows", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            schedule: [{ from: "08:00:00", to: "09:00:00" }],
            effective_schedule: [{ from: "08:00:00", to: "09:00:00" }],
          },
        },
      },
    });

    const card = mountCard(
      { entities: ["sensor.a"], title: "X", card: true },
      hass,
    );

    const spyRows = vi.spyOn(card, "_createDialogRows");

    const row = card._content._rows[0];
    row._content.onclick();

    expect(card._dialog._entity).toBe("sensor.a");
    expect(card._dialog.headerTitle).toBe("A");
    expect(card._dialog._message.innerText).toBe("");
    expect(card._dialog._plus.tagName).toBe("HA-ICON-BUTTON");

    expect(card._dialog._schedule).toEqual([
      { from: "08:00:00", to: "09:00:00" },
    ]);
    expect(spyRows).toHaveBeenCalledTimes(1);
    expect(card._dialog.open).toBe(true);
  });

  test("plus onclick adds null range and triggers row refresh/save", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            schedule: [{ from: "08:00:00", to: "09:00:00" }],
            effective_schedule: [],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);

    card._content._rows[0]._content.onclick();

    const saveSpy = vi.spyOn(card, "_saveBackendEntity");
    const rowsSpy = vi.spyOn(card, "_createDialogRows");

    card._dialog._plus.onclick();
    expect(card._dialog._schedule).toHaveLength(2);
    expect(card._dialog._schedule[1]).toEqual({ from: null, to: null });
    expect(rowsSpy).toHaveBeenCalled();
    expect(saveSpy).toHaveBeenCalledTimes(1);
  });

  test("createDialogHeader close icon closes dialog; more-info dispatches hass-more-info event", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            schedule: [],
            effective_schedule: [],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);

    card._content._rows[0]._content.onclick();
    expect(card._dialog.open).toBe(true);

    const closeIcon = card._dialog.querySelector(
      "ha-icon-button[data-role='dialog-close']",
    );
    const moreInfoIcon = card._dialog.querySelector(
      "ha-icon-button[data-role='more-info']",
    );
    expect(closeIcon).toBeTruthy();
    expect(moreInfoIcon).toBeTruthy();

    closeIcon.onclick();
    expect(card._dialog.open).toBe(false);

    const spy = vi.fn();
    card.addEventListener("hass-more-info", spy);
    card._content._rows[0]._content.onclick();
    moreInfoIcon.onclick();

    expect(spy).toHaveBeenCalledTimes(1);
    const ev = spy.mock.calls[0][0];
    expect(ev.detail).toEqual({ entityId: "sensor.a" });
    expect(card._dialog.open).toBe(false);
  });

  test("toggle change flips disabled flag and calls _saveBackendEntity", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            schedule: [{ from: "08:00:00", to: "09:00:00", disabled: false }],
            effective_schedule: [],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);
    card._content._rows[0]._content.onclick();

    const saveSpy = vi.spyOn(card, "_saveBackendEntity");

    const firstRowEl = card._dialog._scroller.children[0];
    const toggle = firstRowEl.querySelector("ha-switch");
    expect(toggle).toBeTruthy();
    expect(card._dialog._schedule[0].disabled).toBe(false);

    toggle.dispatchEvent(new Event("change"));
    expect(card._dialog._schedule[0].disabled).toBe(true);
    expect(saveSpy).toHaveBeenCalledTimes(1);
  });

  test("remove icon removes row and saves", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            schedule: [
              { from: "08:00:00", to: "09:00:00" },
              { from: "10:00:00", to: "11:00:00" },
            ],
            effective_schedule: [],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);
    card._content._rows[0]._content.onclick();
    expect(card._dialog._schedule).toHaveLength(2);

    const saveSpy = vi.spyOn(card, "_saveBackendEntity");
    const rowsSpy = vi.spyOn(card, "_createDialogRows");

    const firstRowEl = card._dialog._scroller.children[0];
    const rowIcons = firstRowEl.querySelectorAll("ha-icon");
    const removeIcon = rowIcons[rowIcons.length - 1];

    removeIcon.onclick();
    expect(card._dialog._schedule).toHaveLength(1);
    expect(rowsSpy).toHaveBeenCalled();
    expect(saveSpy).toHaveBeenCalled();
  });

  test("_createDialogRow sets consistent marginTop", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            schedule: [],
            effective_schedule: [],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);

    const r0 = card._createDialogRow({ from: "08:00:00", to: "09:00:00" }, 0);
    const r1 = card._createDialogRow({ from: "10:00:00", to: "11:00:00" }, 1);

    expect(r0.style.marginTop).toBe("12px");
    expect(r1.style.marginTop).toBe("12px");
  });
});

describe("DailyScheduleCard - time input behaviors", () => {
  test("_setInputType: time with value, time without value but existing input value, sunrise/sunset modes", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: { friendly_name: "A", effective_schedule: [] },
        },
      },
    });
    const card = mountCard({ entities: ["sensor.a"] }, hass);

    const symbol = document.createElement("ha-icon");
    const input = document.createElement("input");

    card._setInputType("time", symbol, input, "12:34:00");
    expect(symbol._type).toBe("time");
    expect(symbol.icon).toBe("mdi:clock-outline");
    expect(input.type).toBe("time");
    expect(input.value).toBe("12:34");

    input.value = "09:00";
    card._setInputType("time", symbol, input, null);
    expect(input.value).toBe("");

    card._setInputType("sunrise", symbol, input, "+15");
    expect(symbol._type).toBe("sunrise");
    expect(symbol.icon).toBe("mdi:weather-sunny");
    expect(input.type).toBe("number");
    expect(String(input.value)).toBe("15");

    card._setInputType("sunset", symbol, input, "-10");
    expect(symbol._type).toBe("sunset");
    expect(symbol.icon).toBe("mdi:weather-night");
    expect(input.type).toBe("number");
    expect(String(input.value)).toBe("-10");
  });

  test("_createTimeInput: sunrise/sunset onchange with 0 offset keeps only symbol; onchange with unchanged value does not save", () => {
    const hass = createHass();
    const card = mountCard({ entities: ["binary_sensor.a"] }, hass);

    // Prepare dialog + required fields so _saveBackendEntity can run
    card._createDialog();
    card._dialog._entity = "binary_sensor.a";
    card._dialog._schedule = [{ from: "00:00:00", to: "01:00:00" }];

    const spySave = vi
      .spyOn(card, "_saveBackendEntity")
      .mockImplementation(() => {});

    // Case 1: sunrise with 0 offset => value should be "↑" (no +0)
    const range = { from: "↑0", to: null };
    const row = document.createElement("div");
    card._createTimeInput(range, "from", row);
    const symbol = row.children[0];
    const input = row.children[1];
    expect(symbol._type).toBe("sunrise"); // Ensure we're in sunrise mode
    input.value = "0";
    input.onchange();
    expect(range.from).toBe("↑");

    // Case 2: onchange computes same value => should not call save for that change
    spySave.mockClear();
    const range2 = { from: "05:00:00", to: null };
    const row2 = document.createElement("div");
    card._createTimeInput(range2, "from", row2);
    const input2 = row2.children[1];
    input2.value = "05:00";
    input2.onchange(); // computes "05:00:00" which is same
    expect(spySave).not.toHaveBeenCalled();

    spySave.mockRestore();
  });

  test("_createTimeInput: sunset initial branch, negative offsets, and time default path", () => {
    const hass = createHass();
    const card = mountCard({ entities: ["binary_sensor.a"] }, hass);

    card._createDialog();
    card._dialog._entity = "binary_sensor.a";

    const sunsetRange = { from: "↓-5", to: "00:30:00" };
    card._dialog._schedule = [sunsetRange];

    const sunsetRow = document.createElement("div");
    card._createTimeInput(sunsetRange, "from", sunsetRow);

    const sunsetSymbol = sunsetRow.children[0];
    const sunsetInput = sunsetRow.children[1];
    expect(sunsetSymbol._type).toBe("sunset");
    expect(String(sunsetInput.value)).toBe("-5");

    sunsetInput.value = "-15";
    sunsetInput.onchange();
    expect(sunsetRange.from).toBe("↓-15");

    const timeRange = { from: null, to: "02:00:00" };
    card._dialog._schedule = [timeRange];
    const timeRow = document.createElement("div");
    card._createTimeInput(timeRange, "from", timeRow);
    const timeSymbol = timeRow.children[0];
    expect(timeSymbol._type).toBe("time");
  });

  test("_createTimeInput onchange skips offset logic when value becomes empty", () => {
    const hass = createHass();
    const card = mountCard({ entities: ["binary_sensor.a"] }, hass);

    card._createDialog();
    card._dialog._entity = "binary_sensor.a";

    const range = { from: "↑+5", to: "00:10:00" };
    card._dialog._schedule = [range];

    const row = document.createElement("div");
    card._createTimeInput(range, "from", row);

    const input = row.children[1];
    let calls = 0;
    Object.defineProperty(input, "value", {
      get() {
        calls += 1;
        return calls === 1 ? "07:00" : "";
      },
      set() {},
      configurable: true,
    });

    input.onchange();

    expect(range.from).toBe("↑");
  });

  test("_createTimeInput: initializes sunrise/sunset prefixed values, toggles type on symbol click, and onchange updates value", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            schedule: [],
            effective_schedule: [],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);

    card._dialog._entity = "sensor.a";
    card._dialog._schedule = [];
    card._dialog._message.innerText = "";

    const saveSpy = vi.spyOn(card, "_saveBackendEntity");

    const range = { from: "↑+30", to: "↓-15" };
    const row = document.createElement("div");
    card._createTimeInput(range, "from", row);

    const symbol = row.children[0];
    const input = row.children[1];
    expect(symbol._type).toBe("sunrise");
    expect(input.type).toBe("number");
    expect(String(input.value)).toBe("30");

    symbol.onclick();
    expect(symbol._type).toBe("sunset");
    expect(saveSpy).toHaveBeenCalled();

    input.value = "10";
    input.onchange();
    expect(range.from).toBe("↓+10");

    symbol.onclick();
    expect(symbol._type).toBe("time");
    expect(input.type).toBe("time");

    input.value = "07:05";
    input.onchange();
    expect(range.from).toBe("07:05:00");

    symbol.onclick();
    expect(symbol._type).toBe("sunrise");
    expect(input.type).toBe("number");
    expect(range.from).toBe("↑");
  });

  test("_getInputTimeWidth sets and removes dummy input, width capped at 100, and does nothing if already set", () => {
    vi.useFakeTimers();

    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: { friendly_name: "A", effective_schedule: [] },
        },
      },
    });
    const card = mountCard({ entities: ["sensor.a"] }, hass);

    // IMPORTANT:
    // hass-setter already called _getInputTimeWidth() once during mountCard().
    // With fake timers enabled, that first dummy input is still present until we flush timers.
    vi.runAllTimers();

    const original = HTMLInputElement.prototype.getBoundingClientRect;
    HTMLInputElement.prototype.getBoundingClientRect = () => ({ width: 140 });

    // Force re-run of the logic
    card._input_time_width = undefined;

    const beforeChildren = card.children.length;

    card._getInputTimeWidth();

    // +1 dummy added synchronously
    expect(card.children.length).toBe(beforeChildren + 1);

    vi.runAllTimers();

    expect(card._input_time_width).toBe(100);
    // back to original count
    expect(card.children.length).toBe(beforeChildren);

    // already set => no dummy creation
    const before2 = card.children.length;
    card._getInputTimeWidth();
    expect(card.children.length).toBe(before2);

    HTMLInputElement.prototype.getBoundingClientRect = original;
  });
});

describe("DailyScheduleCard - _saveBackendEntity branches", () => {
  test("early returns on missing from/to sets Missing field(s).", () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            schedule: [],
            effective_schedule: [],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);
    card._dialog._entity = "sensor.a";
    card._dialog._schedule = [{ from: null, to: "10:00:00" }];
    card._dialog._message.innerText = "";

    card._saveBackendEntity();

    expect(card._dialog._message.innerText).toBe("Missing field(s).");
    expect(hass.callService).not.toHaveBeenCalled();
  });

  test("success path clears message only if had content", async () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            schedule: [],
            effective_schedule: [],
          },
        },
      },
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);
    card._dialog._entity = "sensor.a";
    card._dialog._schedule = [{ from: "09:00:00", to: "10:00:00" }];
    card._dialog._message.innerText = "old";

    card._saveBackendEntity();
    await flushMicrotasks(3);

    expect(hass.callService).toHaveBeenCalledWith("daily_schedule", "set", {
      entity_id: "sensor.a",
      schedule: [{ from: "09:00:00", to: "10:00:00" }],
    });

    expect(card._dialog._message.innerText).toBe("");
  });

  test("failure path sets message only if changed (covers both branches)", async () => {
    const hass = createHass({
      states: {
        "sensor.a": {
          state: "on",
          attributes: {
            friendly_name: "A",
            schedule: [],
            effective_schedule: [],
          },
        },
      },
      callServiceImpl: vi.fn(() => Promise.reject(new Error("boom"))),
    });

    const card = mountCard({ entities: ["sensor.a"] }, hass);
    card._dialog._entity = "sensor.a";
    card._dialog._schedule = [{ from: "09:00:00", to: "10:00:00" }];
    card._dialog._message.innerText = "";

    // first error sets message
    card._saveBackendEntity();
    await flushMicrotasks(3);
    expect(card._dialog._message.innerText).toBe("boom");

    // second error with same message should keep it the same (covers equality branch)
    card._saveBackendEntity();
    await flushMicrotasks(3);
    expect(card._dialog._message.innerText).toBe("boom");
  });

  test("schedule defaults to [] when _dialog._schedule is missing", async () => {
    const hass = createHass();
    const card = mountCard({ entities: ["binary_sensor.a"] }, hass);
    card._createDialog();
    card._dialog._entity = "binary_sensor.a";
    // intentionally leave _dialog._schedule undefined
    const spy = vi.spyOn(hass, "callService").mockResolvedValue(undefined);

    card._saveBackendEntity();

    // flush microtasks
    await Promise.resolve();
    expect(spy).toHaveBeenCalledWith("daily_schedule", "set", {
      entity_id: "binary_sensor.a",
      schedule: [],
    });

    spy.mockRestore();
  });

  test("missing field(s) branch does not re-set message when already set", () => {
    const hass = createHass();
    const card = mountCard({ entities: ["binary_sensor.a"] }, hass);
    card._createDialog();
    card._dialog._entity = "binary_sensor.a";
    card._dialog._schedule = [{ from: null, to: "01:00:00" }];

    const message = card._dialog._message;
    let setCount = 0;
    const originalText = message.innerText;
    Object.defineProperty(message, "innerText", {
      get() {
        return this._testInnerText;
      },
      set(value) {
        setCount += 1;
        this._testInnerText = value;
      },
      configurable: true,
    });
    message.innerText = originalText;
    setCount = 0;

    // first call sets message
    card._saveBackendEntity();
    expect(message.innerText).toBe("Missing field(s).");
    expect(setCount).toBe(1);

    // second call should early-return but not set again (message already same)
    card._saveBackendEntity();
    expect(setCount).toBe(1);
  });
});

describe("DailyScheduleCard - config form", () => {
  test("getConfigForm exposes the expected schema", () => {
    const configForm = customElements
      .get("daily-schedule-card")
      .getConfigForm();

    expect(configForm.schema).toEqual([
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
    ]);
  });

  test("getConfigForm assertConfig allows configs the visual editor can represent", () => {
    const { assertConfig } = customElements
      .get("daily-schedule-card")
      .getConfigForm();

    expect(() =>
      assertConfig({
        type: "custom:daily-schedule-card",
        title: "Daily Schedule",
        card: true,
        template: "{{ states(entity_id) }}",
        entities: ["binary_sensor.schedule_a", "binary_sensor.schedule_b"],
      }),
    ).not.toThrow();
  });

  test("getConfigForm assertConfig ignores entity validation when entities is not an array", () => {
    const { assertConfig } = customElements
      .get("daily-schedule-card")
      .getConfigForm();

    expect(() =>
      assertConfig({
        type: "custom:daily-schedule-card",
        title: "Daily Schedule",
        card: true,
      }),
    ).not.toThrow();
  });

  test("getConfigForm assertConfig handles missing config", () => {
    const { assertConfig } = customElements
      .get("daily-schedule-card")
      .getConfigForm();

    expect(() => assertConfig()).not.toThrow();
  });

  test("getConfigForm assertConfig switches to YAML mode for unsupported editor shapes", () => {
    const { assertConfig } = customElements
      .get("daily-schedule-card")
      .getConfigForm();

    expect(() =>
      assertConfig({
        entities: [
          {
            entity: "binary_sensor.schedule_a",
            name: "Schedule A",
          },
        ],
      }),
    ).toThrow(/Visual editor is not available for entity options/);

    expect(() =>
      assertConfig({
        entities: [123],
      }),
    ).toThrow(/Visual editor is not available for entity options/);
  });

  test("getConfigForm computeLabel returns friendly labels", () => {
    const { computeLabel } = customElements
      .get("daily-schedule-card")
      .getConfigForm();

    const localize = (key) => key;

    expect(computeLabel({ name: "title" }, localize)).toBe(
      "ui.panel.lovelace.editor.card.generic.title (ui.panel.lovelace.editor.card.config.optional)",
    );
    expect(computeLabel({ name: "entities" }, localize)).toBe(
      "ui.panel.lovelace.editor.card.generic.entities (ui.panel.lovelace.editor.card.config.required)",
    );
    expect(computeLabel({ name: "unknown_option" }, localize)).toBe(
      "unknown_option",
    );
  });
});
