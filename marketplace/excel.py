import re
from io import BytesIO
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape as xml_escape
from zipfile import ZIP_DEFLATED, ZipFile


TEMPLATE_HEADERS = ("Имя", "Телефон")
NAME_HEADER_VARIANTS = {"имя", "name", "фио", "fullname", "fio"}
PHONE_HEADER_VARIANTS = {"телефон", "phone", "mobile", "tel", "telefon", "номер"}


def _normalize_header(value):
    return re.sub(r"[^0-9a-zа-я]+", "", str(value or "").strip().casefold())


def _xlsx_cell(column, row_index, value):
    safe_value = xml_escape(str(value or ""))
    return f'<c r="{column}{row_index}" t="inlineStr"><is><t>{safe_value}</t></is></c>'


def build_excel_template_bytes():
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData><row r="1">'
        f"{_xlsx_cell('A', 1, TEMPLATE_HEADERS[0])}"
        f"{_xlsx_cell('B', 1, TEMPLATE_HEADERS[1])}"
        "</row></sheetData></worksheet>"
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Заявки биржи" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border/></borders><cellStyleXfs count="1"><xf/></cellStyleXfs>'
        '<cellXfs count="1"><xf xfId="0"/></cellXfs>'
        '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
        '</styleSheet>'
    )
    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        '</Types>'
    )
    root_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '</Relationships>'
    )

    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", root_rels_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/styles.xml", styles_xml)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return output.getvalue()


def _shared_strings(archive):
    try:
        shared_strings_xml = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ET.fromstring(shared_strings_xml)
    return [
        "".join(node.text or "" for node in item.findall(".//main:t", namespace))
        for item in root.findall("main:si", namespace)
    ]


def _first_sheet_path(archive):
    namespace = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
    first_sheet = workbook_root.find("main:sheets/main:sheet", namespace)
    if first_sheet is None:
        raise ValueError("В Excel-файле не найден ни один лист")
    relation_id = first_sheet.attrib.get(
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    )
    rels_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    for relation in rels_root.findall("pkg:Relationship", namespace):
        if relation.attrib.get("Id") == relation_id:
            target = relation.attrib.get("Target", "")
            return f"xl/{target.lstrip('/')}" if not target.startswith("xl/") else target
    raise ValueError("Не удалось определить лист Excel для чтения")


def _cell_value(cell, shared_strings, namespace):
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//main:t", namespace))
    value_node = cell.find("main:v", namespace)
    if value_node is None:
        return ""
    raw_value = value_node.text or ""
    if cell_type == "s":
        try:
            return shared_strings[int(raw_value)]
        except (ValueError, IndexError):
            return ""
    return raw_value


def _extract_rows(uploaded_file):
    uploaded_file.seek(0)
    with ZipFile(uploaded_file) as archive:
        sheet_path = _first_sheet_path(archive)
        shared_strings = _shared_strings(archive)
        sheet_xml = archive.read(sheet_path)
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    sheet_root = ET.fromstring(sheet_xml)
    rows = []
    for row in sheet_root.findall(".//main:sheetData/main:row", namespace):
        values = {}
        for cell in row.findall("main:c", namespace):
            column = re.sub(r"\d+", "", cell.attrib.get("r", ""))
            values[column] = _cell_value(cell, shared_strings, namespace).strip()
        if values:
            rows.append(values)
    return rows


def extract_leads_from_excel(uploaded_file):
    rows = _extract_rows(uploaded_file)
    if not rows:
        raise ValueError("Excel-файл пустой")
    header_map = {column: _normalize_header(value) for column, value in rows[0].items()}
    name_column = next((column for column, value in header_map.items() if value in NAME_HEADER_VARIANTS), None)
    phone_column = next((column for column, value in header_map.items() if value in PHONE_HEADER_VARIANTS), None)
    if not name_column or not phone_column:
        raise ValueError("Шаблон должен содержать столбцы 'Имя' и 'Телефон'")

    leads = []
    skipped_rows = 0
    for row in rows[1:]:
        name = (row.get(name_column) or "").strip()
        phone = (row.get(phone_column) or "").strip()
        if not name and not phone:
            continue
        if not name or not phone:
            skipped_rows += 1
            continue
        leads.append({"name": name, "phone": phone})
    if not leads:
        raise ValueError("В Excel-файле нет заполненных строк с именем и телефоном")
    return leads, skipped_rows
