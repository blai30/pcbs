// Copyright 2026 Brian Lai
// SPDX-License-Identifier: GPL-2.0-or-later

#include "quantum.h"
#include "ws2812.h"
#include "analog.h"
#include "led_power.h"

// analogReadPin returns 0 to 1023 on RP2040 (10-bit default).
#define ADC_MAX_COUNT 1023

static bool     has_sense     = false;
// v1.1.0 starts here too and lets the adapt loop climb to LED_SENSE_BUDGET_UA.
static uint32_t budget_ua     = LED_BUDGET_UA;
static uint32_t sense_average = 0;
static rgb_t    frame[RGB_MATRIX_LED_COUNT];
static bool     power_on      = false;
static bool     fault_latched = false;
static bool     suspended     = false;
static bool     settled       = false;
static bool     was_limited   = false;
static uint32_t power_on_time = 0;

static void frame_set_color(int index, uint8_t red, uint8_t green, uint8_t blue) {
    frame[index] = (rgb_t){red, green, blue};
}

static void frame_set_color_all(uint8_t red, uint8_t green, uint8_t blue) {
    for (int i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
        frame_set_color(i, red, green, blue);
    }
}

static uint16_t led_millivolts(void) {
    uint32_t count_sum = 0;
    for (int i = 0; i < LED_SENSE_SAMPLES; i++) {
        count_sum += analogReadPin(LED_SENSE_PIN);
    }
    uint32_t adc_mv = count_sum * 3300 / (ADC_MAX_COUNT * LED_SENSE_SAMPLES);
    return adc_mv * 1000 / LED_SENSE_RATIO_PERMILLE;
}

static void frame_flush(void) {
    if (!power_on) {
        return;
    }
    // Nothing goes out while the switch is still ramping up.
    if (!settled) {
        if (timer_elapsed32(power_on_time) < LED_POWER_SETTLE_MS) {
            return;
        }
        settled = true;
    }
    if (has_sense) {
        sense_average = led_power_smooth(sense_average, led_millivolts());
        budget_ua     = led_power_adapt(budget_ua, sense_average >> LED_SENSE_SMOOTH_SHIFT, LED_SENSE_BUDGET_UA, was_limited);
    }
    uint32_t channel_sum = 0;
    for (int i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
        channel_sum += frame[i].r + frame[i].g + frame[i].b;
    }
    uint16_t scale = led_power_scale(channel_sum, RGB_MATRIX_LED_COUNT, budget_ua);
    was_limited = scale < 256;
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
        // The flush returns while DMA still sends the frame. Wait it out before EN cuts the LEDs' power.
        wait_us(RGB_MATRIX_LED_COUNT * 24 * WS2812_TIMING / 1000 + WS2812_TRST_US);
    }
    gpio_write_pin(LED_POWER_EN_PIN, on);
    power_on      = on;
    power_on_time = timer_read32();
    settled       = false;
    sense_average = 0;
}

void keyboard_pre_init_kb(void) {
    gpio_set_pin_output(LED_POWER_EN_PIN);
    gpio_write_pin_low(LED_POWER_EN_PIN);
    gpio_set_pin_input_high(LED_POWER_FAULT_PIN);
    gpio_set_pin_input_high(BOARD_ID_PIN);
    wait_us(10);
    has_sense = !gpio_read_pin(BOARD_ID_PIN);
    // v1.1.0 drops the pull-up so it draws nothing through the strap. v1.0.0 keeps it so the pin doesn't float.
    if (has_sense) {
        gpio_set_pin_input(BOARD_ID_PIN);
    }
    keyboard_pre_init_user();
}

void housekeeping_task_kb(void) {
    static bool     was_enabled    = false;
    static bool     fault_low      = false;
    static uint32_t fault_low_time = 0;
    bool            enabled        = rgb_matrix_is_enabled();
    // Turning RGB back on clears a fault.
    if (enabled && !was_enabled) {
        fault_latched = false;
    }
    was_enabled = enabled;
    // Latch only a fault that stays low, not noise on the long trace.
    if (power_on && !gpio_read_pin(LED_POWER_FAULT_PIN)) {
        if (!fault_low) {
            fault_low      = true;
            fault_low_time = timer_read32();
        } else if (timer_elapsed32(fault_low_time) >= LED_FAULT_DEBOUNCE_MS) {
            fault_latched = true;
        }
    } else {
        fault_low = false;
    }
    // RGB_MATRIX_TIMEOUT blanks the LEDs after no input. Cut their power too, since they still idle at about 1 mA each.
    bool idle = RGB_MATRIX_TIMEOUT > 0 && last_input_activity_elapsed() > RGB_MATRIX_TIMEOUT;
    set_power(enabled && !suspended && !fault_latched && !idle);
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
