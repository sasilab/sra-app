"""
Used to communicate with a PVPM device that is connected via USB.

Hint: Do not forget to activate the "Data Transfer" after booting the device. (Computer Symbol)
"""

import sys
import time
import struct
import serial
import pandas as pd
import serial.tools.list_ports


def get_usb_ports():
    """
    Checks which ports are currently connected.

    Returns:
    - list of port names
    """
    return [port.device for port in serial.tools.list_ports.comports()]


def measure_iv_curve(com_port: str = "COM3"):
    """
    ## Measure an IV curve using the PVPM 1000CX box.

    Input Arguments:
    - com_port: USB port of the connected PVPM device

    Returns:
    - pandas dataframe with the columns Current and Voltage with the measured IV curve.

     References
    ----------
    - [1] based on communication with pve and reverse engineering their measurement
    ---
    """
    try:
        sp = serial.Serial(
            port=str(com_port),
            baudrate=19200,
            bytesize=8,
            timeout=None,
            stopbits=serial.STOPBITS_ONE,
            parity=serial.PARITY_NONE,
        )

        # waiting for the bootloader to be completed, do not delete!!
        time.sleep(3)

        # send command to pvpm to start the measurement
        sp.write(b"SM4,4;")
        answer = sp.read(3)

        # received MR; means the measurement is ready to be polled
        if answer == b"MR;":
            # start polling data from pvpm
            sp.write(b"RX;")
            time.sleep(0.1)

            # read the total amount of i,v data pairs
            data = sp.read(2)
            # convert received bytes into 2 byte unsigned integer
            iv_pairs = struct.unpack("h", data)
            # store the unsigned int for later use
            amount_iv_pairs = iv_pairs[0]

            # amount of bytes to avoid
            sp.read(49)

            time.sleep(0.1)

            # create the format for later struct usage - f is 4 byte float
            struct_format = 2 * (amount_iv_pairs + 1) * "f"
            bytes_to_read = 2 * (amount_iv_pairs + 1) * 4
            data = sp.read(bytes_to_read)
            i_v_data = struct.unpack(struct_format, data)

            current = i_v_data[1::2]
            voltage = i_v_data[::2]

            rel_diff = ((current[2] - current[1]) / current[1]) * 100
            corrected_current = list(current[:2]) + [
                val + (val * rel_diff / 100) for val in current[2:]
            ]

            return pd.DataFrame({"Current": [corrected_current], "Voltage": [voltage]})
        else:
            print("Connection to PVPM failed")
            sys.exit()
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit()
