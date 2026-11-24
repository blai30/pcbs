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

// Measured on v1.0.0 with the stock daughterboard: 950 mA sagged and turned white orange.
#define LED_BUDGET_UA 800000

// Tied to GND on v1.1.0. Floats high (internal pull-up) on v1.0.0.
#define BOARD_ID_PIN GP0

// LED_5V through R6 (15 kΩ) over R7 (10 kΩ): the ADC sees 0.4 of it.
#define LED_SENSE_PIN GP29
#define LED_SENSE_RATIO_PERMILLE 400
// ADC samples averaged per LED voltage reading, to cut noise against the 100 mV band.
#define LED_SENSE_SAMPLES 4

// With sensing, the budget can rise to the JST SH rating minus the controller.
#define LED_SENSE_BUDGET_UA 950000
