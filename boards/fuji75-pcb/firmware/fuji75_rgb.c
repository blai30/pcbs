// Copyright 2026 Brian Lai
// SPDX-License-Identifier: GPL-2.0-or-later

#include "quantum.h"
#include "ws2812.h"
#include "analog.h"
#include "led_power.h"

// analogReadPin returns 0 to 1023 on RP2040 (10-bit default).
#define ADC_MAX_COUNT 1023

static bool     has_sense     = false;
static uint32_t budget_ua     = LED_BUDGET_UA;
static rgb_t    frame[RGB_MATRIX_LED_COUNT];
static bool     power_on      = false;
static bool     fault_latched = false;
static bool     suspended     = false;
static bool     settled       = false;
static uint16_t power_on_time = 0;

static void frame_set_color(int index, uint8_t red, uint8_t green, uint8_t blue) {
    frame[index] = (rgb_t){red, green, blue};
}

static void frame_set_color_all(uint8_t red, uint8_t green, uint8_t blue) {
    for (int i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
        frame_set_color(i, red, green, blue);
    }
}

static uint16_t led_millivolts(void) {
    uint32_t adc_mv = (uint32_t)analogReadPin(LED_SENSE_PIN) * 3300 / ADC_MAX_COUNT;
    return adc_mv * 1000 / LED_SENSE_RATIO_PERMILLE;
}

static void frame_flush(void) {
    if (!power_on) {
        return;
    }
    // Nothing goes out while the switch is still ramping up.
    if (!settled) {
        if (timer_elapsed(power_on_time) < LED_POWER_SETTLE_MS) {
            return;
        }
        settled = true;
    }
    if (has_sense) {
        budget_ua = led_power_adapt(budget_ua, led_millivolts(), LED_SENSE_BUDGET_UA);
    }
    uint32_t channel_sum = 0;
    for (int i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
        channel_sum += frame[i].r + frame[i].g + frame[i].b;
    }
    uint16_t scale = led_power_scale(channel_sum, RGB_MATRIX_LED_COUNT, budget_ua);
    for (int i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
        ws2812_set_color(i, (frame[i].r * scale) >> 8, (frame[i].g * scale) >> 8, (frame[i].b * scale) >> 8);
    }
    ws2812_flush();
}

const rgb_matrix_driver_t rgb_matrix_driver = {
    .init          = ws2812_init,
    .set_color     = frame_set_color,
    .set_color_all = frame_set_color_all,
    .flush         = frame_flush,
};

static void set_power(bool on) {
    if (on == power_on) {
        return;
    }
    // A dark frame first: v1.0.0 has no switch, so its LEDs would keep the last frame.
    if (!on) {
        ws2812_set_color_all(0, 0, 0);
        ws2812_flush();
    }
    gpio_write_pin(LED_POWER_EN_PIN, on);
    power_on      = on;
    power_on_time = timer_read();
    settled       = false;
}

void keyboard_pre_init_kb(void) {
    gpio_set_pin_output(LED_POWER_EN_PIN);
    gpio_write_pin_low(LED_POWER_EN_PIN);
    gpio_set_pin_input_high(LED_POWER_FAULT_PIN);
    gpio_set_pin_input_high(BOARD_ID_PIN);
    wait_us(10);
    has_sense = !gpio_read_pin(BOARD_ID_PIN);
    budget_ua = has_sense ? LED_SENSE_BUDGET_UA : LED_BUDGET_UA;
    keyboard_pre_init_user();
}

void housekeeping_task_kb(void) {
    static bool was_enabled = false;
    bool        enabled     = rgb_matrix_is_enabled();
    // Turning RGB back on clears a fault.
    if (enabled && !was_enabled) {
        fault_latched = false;
    }
    was_enabled = enabled;
    if (power_on && !gpio_read_pin(LED_POWER_FAULT_PIN)) {
        fault_latched = true;
    }
    set_power(enabled && !suspended && !fault_latched);
    housekeeping_task_user();
}

void suspend_power_down_kb(void) {
    suspended = true;
    set_power(false);
    suspend_power_down_user();
}

void suspend_wakeup_init_kb(void) {
    suspended = false;
    suspend_wakeup_init_user();
}
