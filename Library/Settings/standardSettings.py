import sys
from PyQt5.QtWidgets import QApplication  # swap to PySide2/PySide6 if that's what you use


def get_screen_resolution():
    """Returns (width, height) of the primary screen in pixels, using Qt."""
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    screen = app.primaryScreen()
    geometry = screen.availableGeometry()  # excludes taskbars/docks; use .geometry() for full screen
    width = geometry.width()
    height = geometry.height()

    if created_app:
        app.quit()

    return width, height


def standard_curve_settings():
    """Curve settings with window size/pos scaled to the current screen."""
    screen_w, screen_h = get_screen_resolution()

    win_w = int(screen_w * 0.6)
    win_h = int(screen_h * 0.6)

    pos_x = int(screen_w * 0.1)
    pos_y = int(screen_h * 0.02)

    return {
        'window': {'size': [win_w, win_h], 'pos': [pos_x, pos_y]},
        't0': 1500,
        't1': 2000,
        'bp': False,
        'stopped': False,
        'sortkey': 'treeid',
        'colormap': 'nipy_spectral',
        'legend': True,
    }

def standard_display_settings():
    """Curve settings with window size/pos scaled to the current screen."""
    screen_w, screen_h = get_screen_resolution()

    win_w = int(screen_w * 0.8)
    win_h = int(screen_h * 0.8)

    return {'startProj': [2913, 9214], 'DefMag': ['C200824NB', 'C14'], 'fontsize': 15, 'height': 25, 'windowheight': win_h, 'windowwidth': win_w, 'userbool':True}

def windowsizes():
    """Window sizes with window size/pos scaled to the current screen."""
    screen_w, screen_h = get_screen_resolution()
    win_w = int(screen_w * 0.8)
    win_h = int(screen_h * 0.8)
    settings = windowsettings
    for key in ["editcol", "projectviewer", "plotwindow", "Mainwindow"]:
        settings[key]["height"] = win_h
        settings[key]["width"] = win_w
    return settings


standard_sql_settings = {
    "myhost": "mysql-lip.phys.ethz.ch",
    "projectquery2" : "SELECT \n        CONCAT(db_ams.target_t.sample_nr,\n                _UTF8'.',\n                db_ams.target_t.prep_nr,\n                _UTF8'.',\n                db_ams.target_t.target_nr) AS target_id,\n        db_ams.target_t.*,\n        db_mc14.workproto.TIMEDAT AS timedat,\n db_mc14.workproto.A AS A, db_mc14.workproto.B AS B,     db_ams.preparation_t.step1_method AS step1_method,\n        db_ams.preparation_t.step2_method AS step2_method,\n        db_ams.preparation_t.batch AS batch,\n        db_ams.sample_t.type AS type,\n        db_ams.sample_t.material AS material,\n        db_ams.sample_t.fraction AS fraction,\n        db_ams.sample_t.sampling_date AS sampling_date,\n        db_ams.sample_t.not_tobedated AS not_tobedated,\n        db_ams.sample_t.user_label AS user_label,\n        db_ams.sample_t.user_label_nr AS user_label_nr,\n        db_ams.sample_t.user_desc1 AS user_desc1,\n        db_ams.sample_t.user_desc2 AS user_desc2,\n        db_ams.project_t.project_nr AS project_nr,\n        db_ams.project_t.project AS project,\n        db_ams.project_t.priority AS priority,\n        db_ams.project_t.status AS status,\n        db_ams.project_t.advisor AS advisor,\n        db_ams.project_t.research AS research,\n        db_ams.user_t.user_nr AS user_nr,\n        db_ams.user_t.first_name AS first_name,\n        db_ams.user_t.last_name AS last_name\n    FROM\n        (((((db_ams.sample_t\n        JOIN db_ams.preparation_t)\n        JOIN db_ams.target_t)\n  JOIN db_mc14.workproto)\n        JOIN db_ams.project_t)\n        JOIN db_ams.user_t)\n    WHERE\n         db_ams.sample_t.sample_nr = db_ams.preparation_t.sample_nr\n            AND db_ams.sample_t.sample_nr = db_ams.target_t.sample_nr\n            AND db_ams.preparation_t.prep_nr = db_ams.target_t.prep_nr\n            AND db_ams.sample_t.project_nr = db_ams.project_t.project_nr\n            AND db_ams.project_t.user_nr = db_ams.user_t.user_nr\n            AND db_mc14.workproto.SAMPLE_NR = db_ams.target_t.sample_nr\n            AND db_mc14.workproto.TARGET_NR = db_ams.target_t.target_nr\n            AND db_mc14.workproto.PREP_NR = db_ams.target_t.prep_nr\n            AND db_ams.project_t.project_nr = %i \n\tGROUP BY CONCAT(db_ams.target_t.sample_nr,\n            _UTF8'.',\n            db_ams.target_t.prep_nr,\n            _UTF8'.',\n            db_ams.target_t.target_nr)",
    "projectquery" : "SELECT * FROM db_ams.target_v where db_ams.target_v.project_nr = %i;"
}


standard_table_settings = {
    "fontsize": 10,
    "columns": [
        "target_id",
        "target_pressed",
        "fm",
        "fm_sig",
        "user_label_nr",
        "user_label",
        "c14_age",
        "c14_age_sig",
        "magazine",
        "user_desc2",
        "user_desc1",
        "research",
        "co2_final"
    ],
    "target_id": {
        "Display Name": "Target Id",
        "Format": "%s",
        "Multiplier": None,
        "width": 124
    },
    "fm": {
        "Display Name": "F\u00b9\u2074C",
        "Format": "%.4f",
        "Multiplier": None,
        "width": 87
    },
    "fm_sig": {
        "Display Name": "F\u00b9\u2074C_sig",
        "Format": "%.4f",
        "Multiplier": None,
        "width": 111
    },
    "sample_nr": {
        "Display Name": "Sample Nr.",
        "Format": "%s",
        "Multiplier": None,
        "width": 100
    },
    "fraction": {
        "Display Name": "Fraction",
        "Format": "%s",
        "Multiplier": None,
        "width": 100
    },
    "magazine": {
        "Display Name": "Magazine",
        "Format": "%s",
        "Multiplier": None,
        "width": 179
    },
    "user_label_nr": {
        "Display Name": "User Label Nr.",
        "Format": "%s",
        "Multiplier": None,
        "width": 169
    },
    "c14_age": {
        "Display Name": "\u00b9\u2074C age",
        "Format": "%.3f",
        "Multiplier": None,
        "width": 120
    },
    "c14_age_sig": {
        "Display Name": "\u00b9\u2074C age sig",
        "Format": "%.3f",
        "Multiplier": None,
        "width": 139
    },
    "co2_final": {
        "Display Name": "co2_final",
        "Format": "%s",
        "Multiplier": None,
        "width": 267
    },
    "advisor": {
        "Display Name": "Advisor",
        "Format": "%s",
        "Multiplier": None,
        "width": 100
    },
    "status": {
        "Display Name": "Status",
        "Format": "%s",
        "Multiplier": None,
        "width": 100
    },
    "project": {
        "Display Name": "Project",
        "Format": "%s",
        "Multiplier": None,
        "width": 97
    },
    "dc13": {
        "Display Name": "D13C",
        "Format": "%s",
        "Multiplier": None,
        "width": 100
    },
    "material": {
        "Display Name": "Material",
        "Format": "%s",
        "Multiplier": None,
        "width": 100
    },
    "research": {
        "Display Name": "research",
        "Format": "%s",
        "Multiplier": None,
        "width": 121
    },
    "user_label": {
        "Display Name": "user_label",
        "Format": "%s",
        "Multiplier": None,
        "width": 138
    },
    "target_pressed": {
        "Display Name": "target_pressed",
        "Format": "%s",
        "Multiplier": None,
        "width": 176
    },
    "priority": {
        "Display Name": "priority",
        "Format": "%s",
        "Multiplier": None,
        "width": 100
    },
    "user_desc1": {
        "Display Name": "User decr 1",
        "Format": "%s",
        "Multiplier": None,
        "width": 351
    },
    "user_desc2": {
        "Display Name": "user_desc2",
        "Format": "%s",
        "Multiplier": None,
        "width": 140
    },
    "last_name": {
        "Display Name": "last_name",
        "Format": "%s",
        "Multiplier": None,
        "width": 325
    },
    "timedat": {
        "Display Name": "timedat",
        "Format": "%s",
        "Multiplier": None,
        "width": 512
    },
    "A": {
        "Display Name": "A",
        "Format": "%.2f",
        "Multiplier": None,
        "width": 100
    }
}

standard_proj_plot_Settings = {
    "xkey": "user_label_nr",
    "ykeys": [
        "fm"
    ],
    "xlabel": "user_label_nr",
    "ylabels": [
        "fm"
    ],
    "xmin": "auto",
    "xmax": "auto",
    "ymins": [
        "auto"
    ],
    "ymaxs": [
        "auto"
    ],
    "ycolors": [
        "red"
    ],
    "forms": [
        "s"
    ],
    "Outliertest": False,
    "pval": 0.01,
    "lenwindow": 3,
    "zfactor": 4
}

windowsettings = {
    "editcol": {
        "labels": [
            "load_button",
            "save_button",
            "OK_button",
            "Cancel_button",
            "pB_Add",
            "pB_Remove",
            "pB_Up",
            "pB_Down"
        ]
    },
    "projectviewer": {
        "labels": []
    },
    "plotwindow": {
        "labels": [
            "edit_Button",
            "edit_Button",
            "label_2",
            "error_input",
            "label_3",
            "last_button",
            "next_button",
            "activate_Button",
            "deactivate_Button",
            "adjust_button"
        ]
    },
    "Mainwindow": {
        "labels": [
            "label_2",
            "tab_2",
            "SampleNr",
            "label",
            "sampleEdit",
            "searchButton",
            "plotButton",
            "widthButton",
            "projectLabel",
            "editButton",
            "ProjectNrBox",
            "UserNrBox",
            "UserNameBox",
            "ProjectNameBox",
            "tabWidget",
            "groupBox"
        ]
    }
}