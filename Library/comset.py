from Library.file import read_file, write_file
from typing import Union
from os.path import join
import copy
from Library.Settings.standardSettings import (
    standard_display_settings,
    standard_table_settings,
    standard_proj_plot_Settings,
    windowsizes,
    standard_curve_settings,
    standard_sql_settings
)

DEFAULT_SETTINGS_MAP = {
    "display_settings": standard_display_settings,
    "project_table_settings": standard_table_settings,
    "proj_plot_Settings": standard_proj_plot_Settings,
    "windowsizes": windowsizes,
    "curve_settings" : standard_curve_settings,
    "sql" : standard_sql_settings
}


settingspath = join('Library','Settings')


def read_settings(file_name: str, path: str = settingspath) -> dict:
    default_entry = DEFAULT_SETTINGS_MAP.get(file_name)
    if default_entry is None:
        raise ValueError(
            f"No default settings registered for '{file_name}'. "
            f"Available: {list(DEFAULT_SETTINGS_MAP.keys())}"
        )
    default_data = default_entry() if callable(default_entry) else default_entry
    data = read_file(file_name=file_name, path=path, file_format="json")
    if data is None:
        data = copy.deepcopy(default_data)
        write_settings(data=data, file_name=file_name, path=path)
    else:
        updated = False
        for key in default_data.keys():
            if key not in data:
                data[key] = copy.deepcopy(default_data[key])
                updated = True
        if updated:
            write_settings(data=data, file_name=file_name, path=path)
    return data


def write_settings(data: dict, file_name: str, path: str = settingspath) -> None:
    return write_file(data=data, file_name=file_name, path=path, file_format='json')


def read_data(file_name: str, path: str = "Data") -> Union[dict, None]:
    return read_file(file_name=file_name, path=path, file_format='pickle')


def write_data(data: dict, file_name: str, path: str = "Data") -> None:
    return write_file(data=data, file_name=file_name, path=path, file_format='pickle')

