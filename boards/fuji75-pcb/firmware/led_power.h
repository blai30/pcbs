// Copyright 2026 Brian Lai
// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once

#include <stdbool.h>
#include <stdint.h>

// SK6812 MINI-E datasheet: 12 mA per channel at full value, about 1 mA idle per LED.
#define LED_CHANNEL_UA 12000
#define LED_IDLE_UA 1000

// The factor (out of 256) that brings a frame under budget_ua. 256 leaves it unchanged.
uint16_t led_power_scale(uint32_t channel_sum, uint16_t led_count, uint32_t budget_ua);

// LED voltage band for the adaptive budget (v1.1.0). Below LOW the budget steps down, above HIGH it creeps back up, but only after a frame the budget limited.
#define LED_SENSE_LOW_MV 4500
#define LED_SENSE_HIGH_MV 4600
#define LED_SENSE_MIN_UA 300000
#define LED_SENSE_STEP_DOWN_UA 20000
#define LED_SENSE_STEP_UP_UA 2000

// The next frame's budget from the measured LED voltage, kept between LED_SENSE_MIN_UA and max_ua.
// was_limited is whether the last frame was scaled down; a healthy voltage on a frame that never reached the budget proves no headroom.
uint32_t led_power_adapt(uint32_t budget_ua, uint16_t led_mv, uint32_t max_ua, bool was_limited);

// Each reading's weight in the LED voltage average is 1 / 2^LED_SENSE_SMOOTH_SHIFT. At 60 frames a second that spans about 270 ms, hundreds of PWM periods.
#define LED_SENSE_SMOOTH_SHIFT 4

// Folds one LED voltage reading into a running average kept in mV << LED_SENSE_SMOOTH_SHIFT. Single reads catch one phase of the LED PWM; frames land at unrelated phases, so the average settles on the true mean.
// A zero average starts over from this reading.
uint32_t led_power_smooth(uint32_t average, uint16_t led_mv);
