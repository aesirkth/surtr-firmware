"""
Plot ADC data from a recorded .bin file using the same scaling and channel
mappings as the dashboard (main.py). Requires a config file (ADC channel
scales and labels).
"""
from parser import SurtrParser
import sys
import time
import json
import os
import argparse
import matplotlib.pyplot as plt

# Same voltage/current ranges as main.py
V_START = 0.9
V_END = 4.5
C_START = 4
C_END = 20

# value_id -> (adc_name, channel_num, scale_type). scale_type "v" = voltage, "c" = current.
# Matches main.py: ADC0 ch8/ch9 use value90/value80 (board wiring swap); ADC1 ch8/ch9 use value91/value81.
VALUE_ID_MAP = {
    "value10": ("ADC0", 1, "c"),
    "value20": ("ADC0", 2, "c"),
    "value30": ("ADC0", 3, "c"),
    "value40": ("ADC0", 4, "c"),
    "value50": ("ADC0", 5, "c"),
    "value60": ("ADC0", 6, "c"),
    "value70": ("ADC0", 7, "c"),
    "value90": ("ADC0", 8, "c"),
    "value80": ("ADC0", 9, "c"),
    "value100": ("ADC0", 10, "c"),
    "value110": ("ADC0", 11, "c"),
    "value11": ("ADC1", 1, "c"),
    "value21": ("ADC1", 2, "c"),
    "value31": ("ADC1", 3, "c"),
    "value41": ("ADC1", 4, "c"),
    "value51": ("ADC1", 5, "c"),
    "value61": ("ADC1", 6, "c"),
    "value71": ("ADC1", 7, "c"),
    "value91": ("ADC1", 8, "c"),
    "value81": ("ADC1", 9, "c"),
    "value101": ("ADC1", 10, "c"),
    "value111": ("ADC1", 11, "c"),
}


def load_config(config_path):
    """Load ADC config from JSON. Same structure as main.py / ConfigManager."""
    with open(config_path, "r") as f:
        return json.load(f)


def scale_value(x, scale_type, scale, v_start=V_START, v_end=V_END, c_start=C_START, c_end=C_END):
    """Apply voltage or current scaling using config scale. Matches main.py conversion."""
    if scale_type == "v":
        return scale * (x - v_start) / (v_end - v_start)
    elif scale_type == "c":
        return scale * (x - c_start) / (c_end - c_start)
    else:
        raise ValueError(f"scale_type must be 'v' or 'c', got {scale_type!r}")


def channel_label(adc_name, channel_num, config):
    """Build display label from config, same idea as main.py build_channel_label."""
    channel_key = f"channel{channel_num}"
    label_text = config[adc_name][channel_key].get("label", "")
    if label_text:
        return f"{channel_num}. {label_text}"
    return f"{channel_num}"


def unwrap_time(times):
    """Unwrap time series: detect overflow (time going backwards) and add offset."""
    out = [0.0] * len(times)
    overflow_value = 0.0
    for i in range(1, len(times)):
        if times[i - 1] > times[i]:
            overflow_value += out[i - 1]
            print(f"time overflow at {overflow_value}")
        out[i] = times[i] + overflow_value
    return out


def build_series(parser, config, value_ids):
    """
    Build list of {value_id, label, time_series, data_series} from parser data,
    using config for scale/label and VALUE_ID_MAP for scaling type.
    """
    result = []
    for value_id in value_ids:
        if value_id not in VALUE_ID_MAP:
            raise ValueError(f"unknown value_id {value_id!r}")
        adc_name, channel_num, scale_type = VALUE_ID_MAP[value_id]
        channel_key = f"channel{channel_num}"
        scale = config[adc_name][channel_key].get("scale", 1.0)
        label = channel_label(adc_name, channel_num, config)

        raw_times = parser.data[value_id][0]
        raw_values = parser.data[value_id][1]
        time_series = unwrap_time(raw_times)
        data_series = [
            scale_value(x, scale_type, scale) for x in raw_values
        ]

        result.append({
            "value_id": value_id,
            "label": label,
            "time_series": time_series,
            "data_series": data_series,
        })
    return result


def main():
    parser_arg = argparse.ArgumentParser(description="Plot Surtr ADC data from a .bin file")
    parser_arg.add_argument(
        "data_path",
        help="Path to .bin file (or COM port for live; plot.py typically uses a file)",
    )
    parser_arg.add_argument(
        "-c", "--config",
        default=os.path.join(os.path.dirname(__file__), "adc_config.json"),
        help="Path to ADC config JSON (default: dashboard/adc_config.json)",
    )
    args = parser_arg.parse_args()

    config_path = args.config
    config = load_config(config_path)

    print("parsing...")
    parser = SurtrParser(args.data_path)

    while True:
        if parser.stopped():
            break
        time.sleep(0.1)

    print("generating...")

    # Default plot: left = voltage channels (e.g. thermocouples), right = current channels
    voltage_value_ids = ["value50", "value60", "value70"]
    current_value_ids = ["value80", "value90", "value100", "value110"]

    voltage_series = build_series(parser, config, voltage_value_ids)
    current_series = build_series(parser, config, current_value_ids)

    plt.subplot(1, 2, 1)
    for s in voltage_series:
        plt.plot(s["time_series"], s["data_series"], label=s["label"])
    plt.legend()
    plt.xlabel("time")
    plt.title("Voltage (e.g. thermocouples)")

    plt.subplot(1, 2, 2)
    for s in current_series:
        plt.plot(s["time_series"], s["data_series"], label=s["label"])
    plt.legend()
    plt.xlabel("time")
    plt.title("Current")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
