import matplotlib
matplotlib.use('MacOSX')

import serial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, CheckButtons, Button
import time

# -----------------------------------
# SERIAL PORT
# -----------------------------------


pan_offset = 0

PRE_TRIGGER = 20

print("OPENING SERIAL PORT...")

ser = serial.Serial(
    '/dev/cu.usbmodem103',
    921600,
    timeout=0.01
)

# CLEAR OLD SERIAL DATA
ser.reset_input_buffer()

print("SERIAL PORT OPENED")

# -----------------------------------
# PACKET SETTINGS
# -----------------------------------

HEADER = b'\xAA\x55'

BUF_SAMPLES = 200

PAYLOAD_SIZE = BUF_SAMPLES * 2

# ADC SAMPLE RATE
SAMPLE_RATE = 10000  # Hz

DT = 1.0 / SAMPLE_RATE

print(f"PAYLOAD SIZE = {PAYLOAD_SIZE}")
print(f"SAMPLE RATE = {SAMPLE_RATE} Hz")

# -----------------------------------
# FIGURE
# -----------------------------------

fig, ax = plt.subplots()


DISPLAY_SAMPLES = 30000

current_display_samples = DISPLAY_SAMPLES

# TIME AXIS
x = np.arange(DISPLAY_SAMPLES) * DT

# VOLTAGE BUFFER
y = np.zeros(DISPLAY_SAMPLES, dtype=np.float32)

line, = ax.plot(x, y)

# AXIS LIMITS
ax.set_ylim(-1, 5.0)

ax.set_xlim(0, DISPLAY_SAMPLES * DT)

# LABELS
ax.set_xlabel("Time (s)")
ax.set_ylabel("Voltage (V)")

plt.grid(True)

plt.subplots_adjust(bottom=0.25)

# -----------------------------------
# SLIDER
# -----------------------------------

slider_ax = plt.axes([0.2, 0.1, 0.6, 0.03])

sample_slider = Slider(
    ax=slider_ax,
    label='Display Samples',
    valmin=50,
    valmax=DISPLAY_SAMPLES,
    valinit=DISPLAY_SAMPLES,
    valstep=100
)

# -----------------------------------
# PAN SLIDER
# -----------------------------------

pan_slider_ax = plt.axes([0.2, 0.05, 0.6, 0.03])

pan_slider = Slider(
    ax=pan_slider_ax,
    label='Pan',
    valmin=0,
    valmax=DISPLAY_SAMPLES,
    valinit=0,
    valstep=1
)

# -----------------------------------
# PAN LEFT BUTTON
# -----------------------------------

pan_left_ax = plt.axes([0.85, 0.03, 0.03, 0.03])

pan_left_button = Button(
    pan_left_ax,
    "▼"
)

# -----------------------------------
# PAN RIGHT BUTTON
# -----------------------------------

pan_right_ax = plt.axes([0.85, 0.07, 0.03, 0.03])

pan_right_button = Button(
    pan_right_ax,
    "▲"
)

# -----------------------------------
# CHECKBOX
# -----------------------------------

# FREEZE 

checkbox_ax = plt.axes([0.85, 0.9, 0.08, 0.06])

stop_checkbox = CheckButtons(
    checkbox_ax,
    ['STOP'],
    [False]
)

# CURSOR

cursor_checkbox_ax = plt.axes([0.85, 0.82, 0.10, 0.06])

cursor_checkbox = CheckButtons(
    cursor_checkbox_ax,
    ['CURSORS'],
    [False]
)

# -----------------------------------
# GLOBALS
# -----------------------------------

cursor_mode = False

packet_count = 0

python_freeze = False

TRIGGER_LEVEL = 1.65

trigger_enabled = True

sweep_index = 0

def cursor_callback(label):

    global cursor_mode

    cursor_mode = cursor_checkbox.get_status()[0]

    if cursor_mode:

        h_cursor1.set_visible(True)
        h_cursor2.set_visible(True)
        v_cursor1.set_visible(True)
        v_cursor2.set_visible(True)
        cursor_text.set_visible(True)

        print("CURSORS ENABLED")

    else:

        h_cursor1.set_visible(False)
        h_cursor2.set_visible(False)
        v_cursor1.set_visible(False)
        v_cursor2.set_visible(False)
        cursor_text.set_visible(False)

        print("CURSORS DISABLED")

    fig.canvas.draw_idle()

def update_pan(val):

    global pan_offset

    pan_offset = int(pan_slider.val)

pan_slider.on_changed(update_pan)


def pan_left(event):

    global pan_offset

    pan_offset -= 1

    if pan_offset < 0:
        pan_offset = 0

    pan_slider.set_val(pan_offset)

def pan_right(event):

    global pan_offset

    pan_offset += 1

    max_offset = DISPLAY_SAMPLES - current_display_samples

    if pan_offset > max_offset:
        pan_offset = max_offset

    pan_slider.set_val(pan_offset)

pan_left_button.on_clicked(pan_left)

pan_right_button.on_clicked(pan_right)

cursor_checkbox.on_clicked(cursor_callback)


# -----------------------------------
# FIND VALID PACKET
# -----------------------------------

def find_packet():

    max_search = 500

    for _ in range(max_search):

        byte1 = ser.read(1)

        if len(byte1) == 0:
            return None

        # DEBUG
        # print("BYTE1 =", byte1.hex())

        if byte1 == b'\xAA':

            byte2 = ser.read(1)

            if len(byte2) == 0:
                return None

            # DEBUG
            # print("BYTE2 =", byte2.hex())

            if byte2 == b'\x55':

                # DEBUG
                # print("VALID HEADER")

                payload = ser.read(PAYLOAD_SIZE)

                if len(payload) != PAYLOAD_SIZE:

                    print("INCOMPLETE PAYLOAD")

                    return None

                data = np.frombuffer(
                    payload,
                    dtype='<u2'
                )

                # DEBUG
                # print(data[:10])

                return data

    print("SYNC LOST")

    return None

# -----------------------------------
# TRIGGER DETECTION
# -----------------------------------

def find_trigger(data):

    for i in range(1, len(data)):

        previous_sample = data[i - 1]

        current_sample = data[i]

        # RISING EDGE TRIGGER
        if (
            previous_sample < TRIGGER_LEVEL
            and current_sample >= TRIGGER_LEVEL
        ):

            return i

    return None

# -----------------------------------
# STOP CALLBACK
# -----------------------------------

def stop_callback(label):

    global python_freeze

    stopped = stop_checkbox.get_status()[0]

    python_freeze = stopped

    if stopped:

        print("STOP ENABLED")

        ser.write(b'1')

        print("SENT BYTE = 1")

        time.sleep(0.1)

        # CLEAR REMAINING SERIAL DATA
        ser.reset_input_buffer()

        print("INPUT BUFFER =", ser.in_waiting)

    else:

        print("STOP DISABLED")

        ser.write(b'0')

        print("SENT BYTE = 0")

stop_checkbox.on_clicked(stop_callback)

# -----------------------------------
# SLIDER CALLBACK
# -----------------------------------

def update_display_samples(val):

    global current_display_samples

    current_display_samples = int(sample_slider.val)

    ax.set_xlim(0, current_display_samples * DT)

sample_slider.on_changed(update_display_samples)

# -----------------------------------
# UPDATE LOOP
# -----------------------------------

# -----------------------------------
# UPDATE LOOP
# -----------------------------------

frame_counter = 0

def update(frame):

    global y
    global frame_counter
    global python_freeze
    global packet_count
    global sweep_index

    frame_counter += 1

    latest_data = None

    # -----------------------------------
    # SERIAL DEBUG
    # -----------------------------------

    if frame_counter % 50 == 0:

        print(
            f"SERIAL BYTES WAITING = {ser.in_waiting}, "
            f"PACKETS RECEIVED = {packet_count}"
        )

    # -----------------------------------
    # ACQUISITION
    # -----------------------------------

    if not python_freeze:

        while ser.in_waiting >= (2 + PAYLOAD_SIZE):

            raw_data = find_packet()

            if raw_data is not None:

                latest_data = (
                    raw_data.astype(np.float32) / 4095.0
                ) * 3.3
                
                # print(latest_data[:10])

    # -----------------------------------
    # PROCESS NEW DATA
    # -----------------------------------

    if latest_data is not None:

        packet_count += 1

        if packet_count % 20 == 0:
            print(f"PACKETS RECEIVED = {packet_count}")

        # -----------------------------------
        # TRIGGER MODE
        # -----------------------------------

        if trigger_enabled:

            trigger_index = find_trigger(latest_data)

            # -----------------------------------
            # START NEW SWEEP
            # -----------------------------------

            if sweep_index == 0:

                y[:] = 0

                # TRIGGER FOUND
                if trigger_index is not None:

                    print("TRIGGER FOUND")

                    start = max(0, trigger_index - PRE_TRIGGER)

                    triggered_frame = latest_data[start:]

                    samples_to_write = len(triggered_frame)

                    y[:samples_to_write] = triggered_frame

                    sweep_index = samples_to_write

                # AUTO MODE
                else:

                    print("AUTO SWEEP")

                    y[:BUF_SAMPLES] = latest_data

                    sweep_index = BUF_SAMPLES

            # -----------------------------------
            # CONTINUE SWEEP
            # -----------------------------------

            else:

                end_index = sweep_index + BUF_SAMPLES

                if end_index >= current_display_samples:

                    sweep_index = 0

                    y[:] = 0

                else:

                    y[sweep_index:end_index] = latest_data

                    sweep_index = end_index

        # -----------------------------------
        # NON-TRIGGERED MODE
        # -----------------------------------

        else:

            end_index = sweep_index + BUF_SAMPLES

            if end_index >= current_display_samples:

                sweep_index = 0

                y[:] = 0

            else:

                y[sweep_index:end_index] = latest_data

                sweep_index = end_index

    # -----------------------------------
    # DISPLAY / PAN VIEW
    # -----------------------------------

    if python_freeze:

        start = pan_offset
        end = start + current_display_samples

        if end > DISPLAY_SAMPLES:
            end = DISPLAY_SAMPLES

        visible_y = y[start:end]

        # FIXED TIME AXIS
        visible_x = np.arange(len(visible_y)) * DT

    else:

        visible_y = y[:current_display_samples]

        visible_x = np.arange(len(visible_y)) * DT

    # -----------------------------------
    # UPDATE DISPLAY
    # -----------------------------------

    ax.set_xlim(
        0,
        len(visible_x) * DT
    )

    line.set_data(
        visible_x,
        visible_y
    )

    return line,

# -----------------------------------
# CURSOR CALLBACKS
# -----------------------------------

h_cursor1 = ax.axhline(1.0, ls='--', lw=2)
h_cursor2 = ax.axhline(2.0, ls='--', lw=2)

v_cursor1 = ax.axvline(0.01, ls='--', lw=2)
v_cursor2 = ax.axvline(0.02, ls='--', lw=2)

cursor_text = ax.text(
    0.02,
    0.98,
    "",
    transform=ax.transAxes,
    verticalalignment='top',
    bbox=dict(facecolor='white', alpha=0.8)
)

h_cursor1.set_visible(False)
h_cursor2.set_visible(False)

v_cursor1.set_visible(False)
v_cursor2.set_visible(False)

cursor_text.set_visible(False)



selected_cursor = None

def update_cursor_text():

    h1 = h_cursor1.get_ydata()[0]
    h2 = h_cursor2.get_ydata()[0]

    v1 = v_cursor1.get_xdata()[0]
    v2 = v_cursor2.get_xdata()[0]

    dv = abs(h2 - h1)
    dt = abs(v2 - v1)

    freq = 0

    if dt > 0:
        freq = 1.0 / dt

    cursor_text.set_text(
        f"H1 = {h1:.3f} V\n"
        f"H2 = {h2:.3f} V\n"
        f"ΔV = {dv:.3f} V\n\n"
        f"V1 = {v1:.6f} s\n"
        f"V2 = {v2:.6f} s\n"
        f"ΔT = {dt:.6f} s\n"
        f"Freq = {freq:.2f} Hz"
    )

def on_press(event):

    global selected_cursor

    if not cursor_mode or not python_freeze:
        return

    if event.inaxes != ax:
        return

    x = event.xdata
    y = event.ydata

    x_tol = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.01
    y_tol = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.02

    selected_cursor = None

    # Vertical cursors
    d1 = abs(x - v_cursor1.get_xdata()[0])
    d2 = abs(x - v_cursor2.get_xdata()[0])

    if min(d1, d2) < x_tol:

        selected_cursor = (
            v_cursor1 if d1 < d2 else v_cursor2
        )

    # Horizontal cursors
    else:

        d3 = abs(y - h_cursor1.get_ydata()[0])
        d4 = abs(y - h_cursor2.get_ydata()[0])

        if min(d3, d4) < y_tol:

            selected_cursor = (
                h_cursor1 if d3 < d4 else h_cursor2
            )
def on_motion(event):

    global selected_cursor

    if selected_cursor is None:
        return

    if event.inaxes != ax:
        return

    if selected_cursor in [v_cursor1, v_cursor2]:

        selected_cursor.set_xdata(
            [event.xdata, event.xdata]
        )

    else:

        selected_cursor.set_ydata(
            [event.ydata, event.ydata]
        )
        
    update_cursor_text()

    fig.canvas.draw_idle()

def on_release(event):

    global selected_cursor

    selected_cursor = None

# -----------------------------------
# CONNECT MOUSE EVENTS
# -----------------------------------

fig.canvas.mpl_connect(
    'button_press_event',
    on_press
)

fig.canvas.mpl_connect(
    'motion_notify_event',
    on_motion
)

fig.canvas.mpl_connect(
    'button_release_event',
    on_release
)

# -----------------------------------
# ANIMATION
# -----------------------------------

print("STARTING ANIMATION")

update_cursor_text()

ani = FuncAnimation(
    fig,
    update,
    interval=50,
    blit=False,
    cache_frame_data=False
)

print("OPENING WINDOW")

plt.show()

print("WINDOW CLOSED")