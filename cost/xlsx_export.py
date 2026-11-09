from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


def _cell(ref, value=None, style=0, formula=None):
    attributes = f' r="{ref}" s="{style}"'
    if formula:
        return f"<c{attributes}><f>{escape(formula)}</f><v>0</v></c>"
    if value is None:
        return f"<c{attributes}/>"
    if isinstance(value, (int, float)) or value.__class__.__name__ == "Decimal":
        return f"<c{attributes}><v>{value}</v></c>"
    return f'<c{attributes} t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'


def build_salary_workbook(title, rows):
    """Build the payroll statement in the established ten-column layout."""
    headers = [
        "ФИО",
        "ПИН",
        "Расчётная сумма",
        "Оклад за месяц",
        "Оклад за период",
        "Процент",
        "Начислено по проценту",
        "Премия/штраф/аванс",
        "Итого",
        "Подпись",
    ]
    sheet_rows = [
        '<row r="1" ht="30" customHeight="1">' + _cell("A1", title, style=1) + "</row>",
        '<row r="2"></row>',
        '<row r="3" ht="48" customHeight="1">'
        + "".join(_cell(f"{column}3", value, style=2) for column, value in zip("ABCDEFGHIJ", headers))
        + "</row>",
    ]

    for row_number, row in enumerate(rows, start=4):
        monthly_salary = row["bet_value"] if row["uses_fixed"] else None
        period_salary = row["period_fixed_salary"] if row["uses_fixed"] else None
        percent = row["percent_value"] if row["uses_percent"] else None
        percent_salary = row["percent_salary"] if row["uses_percent"] else None
        cells = [
            _cell(f"A{row_number}", row["name"], style=3),
            _cell(f"B{row_number}", style=4),
            _cell(f"C{row_number}", row["calculation_amount"], style=5),
            _cell(f"D{row_number}", monthly_salary, style=5),
            _cell(f"E{row_number}", period_salary, style=5),
            _cell(f"F{row_number}", percent, style=9),
            _cell(f"G{row_number}", percent_salary, style=5),
            _cell(f"H{row_number}", style=5),
            _cell(f"I{row_number}", style=6, formula=f"E{row_number}+G{row_number}+H{row_number}"),
            _cell(f"J{row_number}", style=7),
        ]
        sheet_rows.append(
            f'<row r="{row_number}" ht="30" customHeight="1">'
            + "".join(cells)
            + "</row>"
        )

    sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="3" topLeftCell="A4" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <cols>
    <col min="1" max="1" width="30" customWidth="1"/><col min="2" max="2" width="12" customWidth="1"/>
    <col min="3" max="3" width="18" customWidth="1"/><col min="4" max="5" width="17" customWidth="1"/>
    <col min="6" max="6" width="12" customWidth="1"/><col min="7" max="7" width="22" customWidth="1"/>
    <col min="8" max="8" width="20" customWidth="1"/><col min="9" max="9" width="15" customWidth="1"/>
    <col min="10" max="10" width="18" customWidth="1"/>
  </cols>
  <sheetData>{''.join(sheet_rows)}</sheetData>
  <mergeCells count="1"><mergeCell ref="A1:J1"/></mergeCells>
  <pageMargins left="0.25" right="0.25" top="0.5" bottom="0.5" header="0.2" footer="0.2"/>
  <pageSetup orientation="landscape" fitToWidth="1" fitToHeight="0"/>
</worksheet>'''

    styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <numFmts count="2"><numFmt numFmtId="164" formatCode="# ##0.00"/><numFmt numFmtId="165" formatCode="0.000"/></numFmts>
  <fonts count="3">
    <font><sz val="11"/><name val="Times New Roman"/></font>
    <font><b/><sz val="16"/><name val="Times New Roman"/></font>
    <font><b/><sz val="11"/><name val="Times New Roman"/></font>
  </fonts>
  <fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFFF066"/><bgColor indexed="64"/></patternFill></fill></fills>
  <borders count="2"><border/><border><left style="thin"/><right style="thin"/><top style="thin"/><bottom style="thin"/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="10">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="2" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="2" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="0" fillId="2" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="164" fontId="2" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment horizontal="left" vertical="center"/></xf>
    <xf numFmtId="165" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyAlignment="1"><alignment vertical="center"/></xf>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''

    files = {
        "[Content_Types].xml": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>''',
        "_rels/.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>''',
        "xl/workbook.xml": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Ведомость" sheetId="1" r:id="rId1"/></sheets><calcPr calcId="191029" fullCalcOnLoad="1" forceFullCalc="1"/></workbook>''',
        "xl/_rels/workbook.xml.rels": '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>''',
        "xl/worksheets/sheet1.xml": sheet_xml,
        "xl/styles.xml": styles_xml,
    }
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path, content in files.items():
            archive.writestr(path, content.encode("utf-8"))
    return output.getvalue()
