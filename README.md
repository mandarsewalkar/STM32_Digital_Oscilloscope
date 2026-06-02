# STM32 Digital Oscilloscope

A real-time digital oscilloscope built using STM32F446RE, ADC DMA acquisition, UART DMA streaming, and a Python-based visualization interface.

## Overview

This project samples analog signals using the STM32 ADC triggered by a hardware timer. Samples are collected using DMA and streamed to a PC over UART. A Python GUI receives the data, reconstructs packets, and displays the waveform in real time.

The project was built to gain hands-on experience with:

- STM32 peripherals
- ADC and DAC
- DMA
- Timers
- UART communication
- Real-time data acquisition
- Signal visualization using Python

## Features

- Timer-triggered ADC sampling
- DMA-based data acquisition
- UART DMA streaming
- Square & Sin waveform generation for testing
- Packet synchronization using headers
- Real-time waveform display
- Trigger mode
- Freeze mode
- Horizontal and vertical measurement cursors
- Frequency measurement using cursors
- Pan and zoom controls

## Hardware

- STM32F446RE
- USB UART connection
- Analog input source / STM32F446RE

## Software

### Firmware

- STM32CubeIDE
- STM32CubeMX

### PC Application

- Python 3.13
- NumPy
- Matplotlib
- PySerial

## Project Structure

Firmware/

- STM32CubeIDE project
- ADC, DMA, UART, Timer, and DAC configuration

Python_GUI/

- Real-time oscilloscope GUI with Trigger, Cursor, Freeze mechanism

Images/

- Screenshots of GUI

## How It Works

1. Timer 2 triggers ADC conversions at a fixed sampling rate.
2. ADC samples are transferred into memory using DMA.
3. Data is packed and transmitted over UART using DMA.
4. Python receives packets through the serial port.
5. Packets are decoded and displayed as a waveform.
6. Triggering and cursor measurements are performed on the PC.

## Future Improvements

- Increasing STM - PC transmission speed
- FFT spectrum analyzer
- Multiple channels

## Limitation (ver 1)

- Can't plot sinwave with less that 500Hz freq accurately
- Voltage span limited from 0 - 3.3v
- Fixed sampling rate for ADC
