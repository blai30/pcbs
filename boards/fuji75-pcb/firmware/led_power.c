// Copyright 2026 Brian Lai
// SPDX-License-Identifier: GPL-2.0-or-later

#include "led_power.h"

uint16_t led_power_scale(uint32_t channel_sum, uint16_t led_count, uint32_t budget_ua) {
    uint32_t idle_ua = (uint32_t)led_count * LED_IDLE_UA;
    if (idle_ua >= budget_ua) {
        return 0;
    }
    uint32_t available_ua = budget_ua - idle_ua;
    uint64_t channel_ua = (uint64_t)channel_sum * LED_CHANNEL_UA / 255;
    if (channel_ua <= available_ua) {
        return 256;
    }
    return (uint16_t)((uint64_t)available_ua * 256 / channel_ua);
}

uint32_t led_power_adapt(uint32_t budget_ua, uint16_t led_mv, uint32_t max_ua) {
    if (led_mv < LED_SENSE_LOW_MV) {
        return budget_ua > LED_SENSE_MIN_UA + LED_SENSE_STEP_DOWN_UA ? budget_ua - LED_SENSE_STEP_DOWN_UA : LED_SENSE_MIN_UA;
    }
    if (led_mv > LED_SENSE_HIGH_MV) {
        return budget_ua + LED_SENSE_STEP_UP_UA < max_ua ? budget_ua + LED_SENSE_STEP_UP_UA : max_ua;
    }
    return budget_ua;
}
