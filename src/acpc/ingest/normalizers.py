class InputValidationError(ValueError):
    pass

def _as_float(raw, key, default=0.0):
    value = raw.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise InputValidationError(f"Metric {key} is not numeric: {value!r}") from exc

def normalize_modbus(raw_data):
    return {
        "dc_power_w": _as_float(raw_data, "reg_40083"),
        "temp_inverter_c": _as_float(raw_data, "reg_40103"),
        "daily_yield_kwh": _as_float(raw_data, "reg_40110", 0.0),
        "insulation_mohm": _as_float(raw_data, "reg_40111", 0.0),
    }

def normalize_mqtt(raw_data):
    return {
        "dc_power_w": _as_float(raw_data, "power_kw") * 1000.0,
        "temp_inverter_c": _as_float(raw_data, "inv_temp_c"),
        "daily_yield_kwh": _as_float(raw_data, "daily_yield_kwh", 0.0),
        "insulation_mohm": _as_float(raw_data, "insulation_mohm", 0.0),
    }

def normalize(protocol, raw_data):
    protocol = protocol.upper()
    if protocol == "MODBUS_TCP":
        return normalize_modbus(raw_data)
    if protocol == "MQTT":
        return normalize_mqtt(raw_data)
    raise InputValidationError(f"Unknown protocol: {protocol}")
