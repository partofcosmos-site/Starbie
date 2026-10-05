# Starbie devlog

A small motion-controlled digital pet built for week 1 of Half Life.

| Week | Tier | Track | Status |
| :---: | :---: | :---: | :---: |
| Week 1 | Tier 1 | Starter | In progress |

---

## 2026-10-04 - Schematic capture and component wiring

**3.5h logged**

![Starbie Front](Renders/Starbie%20Front.png)

I started week 1 of Half Life by following the Starbie guide. The goal is to build a motion-controlled desktop pet using a Seeed Studio XIAO ESP32-C3.

First step was setting up KiCad and importing the care package symbol and footprint libraries. The care package had custom footprints for the XIAO board and the Cherry MX style switches.

In the schematic editor, I dropped down the XIAO ESP32-C3 symbol and started wiring nets:
- Connected the 0.96 inch SSD1306 OLED to 3.3V, GND, and the I2C bus on GPIO6 (SDA) and GPIO7 (SCL).
- Tied the MPU-6050 accelerometer and gyroscope to the exact same I2C lines so both chips share the two bus pins without wasting GPIO.
- Added the DHT11 temperature and humidity sensor on GPIO4. I put a 10k resistor between the 3.3V line and the data pin so the sensor line doesn't float when idle.
- Added four Cherry MX switch symbols connected between GPIO pins (D0, D1, D3, D10) and ground. By enabling the internal pull-up resistors in the microcontroller, I avoided needing extra external resistors for each key.

After finishing the connections, I ran the footprint assignment tool to link every symbol to its physical footprint.

---

## 2026-10-05 - Star board layout and JLCPCB DRC checks

**3.5h logged**

![Starbie Back](Renders/Starbie%20Back.png)

Once the schematic passed with zero unconnected pins, I opened the PCB editor and imported the nets from the schematic.

All the parts landed in a big pile in the center of the sheet. I drew out the custom star-shaped boundary on the Edge.Cuts layer and started placing components:
- Centered the OLED display in the middle so the screen is front and center.
- Placed the four mechanical keyboard switches on the outer corners where they are easy to press.
- Placed the MPU-6050 right near the center of the board so tilt readings reflect the actual rotation axis of the gadget.
- Positioned the Seeed XIAO ESP32-C3 on the back side with its USB-C port accessible along the bottom edge for easy plugging.

For trace routing, I kept power tracks at 20 mil to handle current spikes from the display and sensors, while keeping signal traces at 10 mil. I ran the KiCad Design Rules Check against JLCPCB tolerances (6 mil trace/space minimum) and cleared all DRC errors. Then I exported RS-274X Gerbers and created the manufacturing zip.

---

## 2026-10-06 - Firmware testing and tilt eye physics

**3.5h logged**

![Starbie Render](Renders/Starbie%20Render.png)

With the hardware design completed and exported, I focused on testing the firmware in the browser simulator and in Arduino IDE.

The pet uses a procedural eye animation system rendered on the 128x64 OLED:
- The MPU-6050 reads X and Y acceleration continuously. When you tilt the board, the pupil offsets shift proportionally, so Starbie appears to look wherever you tilt the PCB.
- I wrote a simple delta-G calculation for shake detection. If the total acceleration vector changes faster than 1.8G within 100 milliseconds, Starbie switches into a dizzy expression with swirling eyes.
- The DHT11 readings get polled every two seconds. If the ambient temperature goes above 30 degrees Celsius, the pet switches to an overheated face.

Testing the HTML simulator in `Firmware/simulator.html` made it easy to dial in the smoothing filters for accelerometer jitter before flashing the real XIAO ESP32-C3 board over USB-C.
