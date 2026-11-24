// Copyright 2026 Brian Lai
// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once

#include <stdint.h>

// SK6812 MINI-E datasheet: 12 mA per channel at full value, about 1 mA idle per LED.
#define LED_CHANNEL_UA 12000
#define LED_IDLE_UA 1000

// The factor (out of 256) that brings a frame under budget_ua. 256 leaves it unchanged.
uint16_t led_power_scale(uint32_t channel_sum, uint16_t led_count, uint32_t budget_ua);
