# Starbie

![Starbie Render](Renders/Starbie%20Render.png)

Starbie is a small desk pet that reacts to movement. Instead of using buttons to click through menus, you interact with it by tilting and shaking the board. It runs on a Seeed Studio XIAO ESP32-C3 and shows its face on a 0.96 inch OLED screen.

This project is built for week 1 of [Half Life](https://halflife.hackclub.com/), an accelerator by Hack Club where you build hardware and earn a 3D printer.

---

## What it does

- **Tilt-tracked eyes:** An MPU-6050 accelerometer tracks gravity. As you tip the board forward, backward, or side to side, the pet's eyes look in that direction.
- **Shake reactions:** Quick shakes spike the accelerometer readings, triggering surprised or dizzy eye animations on the screen.
- **Room climate checks:** A DHT11 sensor reads temperature and humidity so you can check if your room is too hot or dry.
- **Mechanical keys:** Four Cherry MX switches let you switch modes and trigger actions with tactile feedback.
- **Browser simulator:** You can test the eye physics and menus directly in your browser using [Firmware/simulator.html](Firmware/simulator.html) before uploading code.

---

## Photos

| Front View | Back View |
| :---: | :---: |
| ![Starbie Front](Renders/Starbie%20Front.png) | ![Starbie Back](Renders/Starbie%20Back.png) |

---

## Parts list

Everything fits under the $30 budget cap for Half Life Tier 1:

| Part | Qty | Price (USD) | Link | Notes |
| :--- | :---: | :---: | :--- | :--- |
| Seeed Studio XIAO ESP32-C3 | 1 | $5.00 | [Seeed Studio](https://www.seeedstudio.com/Seeed-XIAO-ESP32C3-p-5431.html) | RISC-V microcontroller with USB-C |
| 0.96 inch I2C OLED (SSD1306) | 1 | $2.50 | [Amazon](https://www.amazon.com/dp/B0GBVWBWCR) | 128x64 display at address 0x3C |
| MPU-6050 6-axis IMU | 1 | $2.29 | [Amazon](https://www.amazon.com/dp/B0943SGP34) | Accelerometer and gyro on I2C address 0x68 |
| DHT11 temperature and humidity sensor | 1 | $3.33 | [Amazon](https://www.amazon.com/dp/B0BLG7R99R) | Single-pin digital sensor |
| Cherry MX compatible switches | 4 | $0.72 | [Amazon](https://www.amazon.com//dp/B0FQP8VYX4) | 4 mechanical keys ($0.18 each) |
| Keycaps | 4 | $2.40 | [Amazon](https://www.amazon.com/dp/B0CQ2VLMVY) | Standard cross-stem caps |
| 10k resistor | 1 | $0.05 | [Amazon](https://www.amazon.com/dp/B0B4JFPHTW) | Pull-up resistor on the DHT11 data line |
| Custom 2-layer PCB | 1 | $10.00 | [JLCPCB](https://www.jlcpcb.com/) | 2-layer FR-4 board fabrication |
| **Total** | | **$24.95** | | |

Full CSV data is in [BOM.csv](BOM.csv) and [bom_parts.csv](bom_parts.csv).

---

## Pin connections

All components connect to the Seeed XIAO ESP32-C3 running at 3.3V:

| Component | Pin | XIAO Pin | Type | Notes |
| :--- | :--- | :--- | :--- | :--- |
| OLED Display | SDA | D4 (GPIO6) | I2C Data | 400kHz shared bus |
| OLED Display | SCL | D5 (GPIO7) | I2C Clock | Pull-ups on module |
| OLED Display | VCC / GND | 3V3 / GND | Power | 3.3V rail |
| MPU-6050 IMU | SDA | D4 (GPIO6) | I2C Data | Shares I2C bus with display |
| MPU-6050 IMU | SCL | D5 (GPIO7) | I2C Clock | |
| MPU-6050 IMU | VCC / GND | 3V3 / GND | Power | 3.3V rail |
| DHT11 Sensor | DATA | D2 (GPIO4) | Digital IO | 10k pull-up to 3.3V |
| Switch 1 | Pin 1 | D0 (GPIO2) | Input | Active-low with internal pull-up |
| Switch 2 | Pin 1 | D1 (GPIO3) | Input | Active-low with internal pull-up |
| Switch 3 | Pin 1 | D3 (GPIO5) | Input | Active-low with internal pull-up |
| Switch 4 | Pin 1 | D10 (GPIO10)| Input | Active-low with internal pull-up |

---

## PCB design files

The board was designed in KiCad using the official footprints and symbols:

- Schematic source: [PCB/Starbie.kicad_sch](PCB/Starbie.kicad_sch)
- Board layout: [PCB/Starbie.kicad_pcb](PCB/Starbie.kicad_pcb)
- KiCad project: [PCB/Starbie.kicad_pro](PCB/Starbie.kicad_pro)
- Manufacturing Gerbers: [gerbers.zip](gerbers.zip) and [PCB/production/Starbie Gerbers V1.0.zip](PCB/production/Starbie%20Gerbers%20V1.0.zip)

Board specs:
- Dimensions: Custom star shape fitting within 100x100 mm
- Layer count: 2 layers (top and bottom copper)
- Material: FR-4, 1.6 mm thickness
- Minimum trace and space: 6 mil / 6 mil
- Surface finish: Lead-free HASL

---

## How to build and flash

### 1. Arduino IDE configuration
1. Install Arduino IDE 2.0 or newer.
2. In Preferences, add the ESP32 board manager URL:
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
3. Open Tools > Board > Boards Manager, search for `esp32`, and install the package.
4. Select `XIAO_ESP32C3` from the board menu.

### 2. Install libraries
Install these libraries through the Library Manager:
- `Adafruit SSD1306`
- `Adafruit GFX Library`
- `Adafruit MPU6050`
- `Adafruit BusIO`
- `DHT sensor library`

### 3. Flash the code
1. Open [Firmware/Starbie/Starbie.ino](Firmware/Starbie/Starbie.ino).
2. Connect your board over USB-C.
3. Select your serial port and hit Upload.

---

## Repository layout

- `PCB/` contains KiCad schematic, layout, and component libraries.
- `Firmware/` contains the Arduino sketch and the browser simulator.
- `Renders/` contains 3D renders of the front and back of the board.
- `Week 1 Guide.md` contains the beginner walkthrough guide.
- `BOM.csv` contains the parts list.
- `gerbers.zip` contains production files ready for JLCPCB.
