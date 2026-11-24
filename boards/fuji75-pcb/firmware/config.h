// Copyright 2026 Brian Lai
// SPDX-License-Identifier: GPL-2.0-or-later

#pragma once

// The custom driver skips the automatic WS2812 LED count.
#define WS2812_LED_COUNT RGB_MATRIX_LED_COUNT

// LED power switch U6 (v1.1.0). Both pins are unconnected on v1.0.0.
#define LED_POWER_EN_PIN GP16
#define LED_POWER_FAULT_PIN GP17

// Time for U6's soft-start before the first frame.
#define LED_POWER_SETTLE_MS 5

// The JST SH contacts are rated 1 A. The controller uses about 50 mA of that.
#define LED_BUDGET_UA 950000
