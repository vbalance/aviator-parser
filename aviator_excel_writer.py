import xlwings as xw
from datetime import datetime
from string import ascii_uppercase

HEADER = {
    "Round number": 15,
    "Result": 8,
    "Datetime": 20,
    "Server seed": 15,
    "Player 1 Name": 13.14,
    "Player 1 Seed": 12.14,
    "Player 2 Name": 13.14,
    "Player 2 Seed": 12.14,
    "Player 3 Name": 13.14,
    "Player 3 Seed": 12.14,
    "Concatenated hash": 19,
    "Result HEX": 19,
    "Result Decimal": 19
}

def open_document(filename: str = None):
    dt = datetime.now()
    wb = xw.Book(filename)
    sheet = wb.sheets[0]

    wb.app.display_alerts = False

    sheet['A1'].value = list(HEADER.keys())

    for i, (column_name, column_width) in enumerate(HEADER.items()):
        sheet.range(f"{ascii_uppercase[i]}:{ascii_uppercase[i]}").column_width = column_width

    if filename is None:
        wb.save(f"{dt.day:02}-{dt.month:02}-{dt.year}T{dt.hour:02}-{dt.minute:02}-{dt.second:02}.xlsx")

    return wb, sheet

def write_payout_info(sheet: xw.Sheet, payout_info):
    new_row = sheet.used_range.last_cell.row + 1

    sheet[f"C{new_row}"].number_format = "dd.mm.yyyy hh:mm:ss"
    sheet[f"A{new_row}"].number_format = "@"
    sheet[f"M{new_row}"].number_format = "@"

    sheet[f"A{new_row}"].value = [
        payout_info.round_number,
        payout_info.result,
        payout_info.dt,
        payout_info.server_seed,
        payout_info.client_seeds[0].name,
        payout_info.client_seeds[0].seed,
        payout_info.client_seeds[1].name,
        payout_info.client_seeds[1].seed,
        payout_info.client_seeds[2].name,
        payout_info.client_seeds[2].seed,
        payout_info.concat_hash,
        payout_info.result_hex,
        payout_info.result_decimal
    ]
