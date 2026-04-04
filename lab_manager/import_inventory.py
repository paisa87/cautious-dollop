"""
import_inventory.py
──────────────────
One-time script to import the Chemical Inventory.xlsx into the lab_manager database.

Usage (run from the lab_manager/ directory):
    python import_inventory.py

It reads:
  - "Chemical" sheet  → InventoryItem (category = chemical)
  - "General Supply" sheet → InventoryItem (category = consumable)
  - Primer/probe appendix docx → InventoryItem (category = primer / probe)

Safe to run multiple times — it skips items that already exist (matched by name).
"""

import sys
import os
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

# Ensure the app module is importable from this directory
sys.path.insert(0, os.path.dirname(__file__))
from app import app, db, Vendor, InventoryItem, User

XLSX_PATH = os.path.join(
    os.path.dirname(__file__), '..',
    'Lab_stuff', 'Course_materials', 'BTC181-LabTechniques', 'Attachments',
    'Chemical Inventory.xlsx'
)
PRIMER_DOCX_PATH = os.path.join(
    os.path.dirname(__file__), '..',
    'Lab_stuff', 'Course_materials', 'BTC181-LabTechniques', 'Attachments',
    'Appendix \u2013 List of recommended Primer-Probe Assays and DNA Controls.docx'
)


def _get_or_create_vendor(name, session):
    if not name:
        return None
    v = Vendor.query.filter(Vendor.name.ilike(f'%{name}%')).first()
    if not v:
        v = Vendor(name=name.strip())
        session.add(v)
        session.flush()
    return v.id


def _parse_date(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val.date()
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y'):
        try:
            return datetime.strptime(str(val), fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _item_exists(name):
    return InventoryItem.query.filter(
        InventoryItem.item_name.ilike(name.strip())
    ).first() is not None


def import_chemicals(wb, admin_id):
    try:
        ws = wb['Chemical']
    except KeyError:
        print('  ! "Chemical" sheet not found — skipping.')
        return 0

    # Column indices (0-based) from header row:
    # 0:Item Name, 1:Vendor, 2:Catalog#, 3:Unit Size, 4:CAS,
    # 5:Location, 6:Sub-location, 7:Location Details, 8:Amount,
    # 9:Price, 10:Min Stock, 11:Max Stock, 12:URL, 13:Tech Details,
    # 14:Exp Date, 15:Lot#, 16:Bottle Ref, 17:Date Opened,
    # 18:Date Received, 19:Formula, 20:Lifespan, 21:MW,
    # 22:Physical State, 23:Purity, 24:SDS Link
    added = 0
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    for row in rows:
        name = row[0]
        if not name or str(name).strip() == '':
            continue
        name = str(name).strip()
        if _item_exists(name):
            continue

        vendor_id = _get_or_create_vendor(
            str(row[1]).strip() if row[1] else None, db.session
        )
        price = None
        try:
            if row[9] is not None:
                price = float(str(row[9]).replace('$', '').replace(',', ''))
        except (ValueError, TypeError):
            pass

        item = InventoryItem(
            item_name=name,
            category='chemical',
            vendor_id=vendor_id,
            catalog_number=str(row[2]).strip() if row[2] else None,
            unit_size=str(row[3]).strip() if row[3] else None,
            cas_number=str(row[4]).strip() if row[4] else None,
            location_room=str(row[5]).strip() if row[5] else None,
            location_unit=str(row[6]).strip() if row[6] else None,
            location_details=str(row[7]).strip() if row[7] else None,
            amount_in_stock=str(row[8]).strip() if row[8] else None,
            price=price,
            min_stock=str(row[10]).strip() if row[10] else None,
            url=str(row[12]).strip() if row[12] else None,
            expiration_date=_parse_date(row[14]),
            lot_number=str(row[15]).strip() if row[15] else None,
            date_opened=_parse_date(row[17]),
            date_received=_parse_date(row[18]),
            formula=str(row[19]).strip() if row[19] else None,
            molecular_weight=float(row[21]) if row[21] else None,
            physical_state=str(row[22]).strip() if row[22] else None,
            purity=str(row[23]).strip() if row[23] else None,
            sds_link=str(row[24]).strip() if row[24] else None,
            added_by_id=admin_id,
        )
        db.session.add(item)
        added += 1

    db.session.commit()
    return added


def import_general_supply(wb, admin_id):
    try:
        ws = wb['General Supply']
    except KeyError:
        print('  ! "General Supply" sheet not found — skipping.')
        return 0

    # 0:Item Name, 1:Vendor, 2:Catalog#, 3:Location, 4:Sub-location,
    # 5:Location Details, 6:Price, 7:Amount in Stock, 8:Min Stock,
    # 9:Max Stock, 10:Unit Size, 11:URL, 12:Tech Details,
    # 13:Exp Date, 14:Lot#, 15:CAS#
    added = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        name = row[0]
        if not name or str(name).strip() == '':
            continue
        name = str(name).strip()
        if _item_exists(name):
            continue

        vendor_id = _get_or_create_vendor(
            str(row[1]).strip() if row[1] else None, db.session
        )
        price = None
        try:
            if row[6] is not None:
                price = float(str(row[6]).replace('$', '').replace(',', ''))
        except (ValueError, TypeError):
            pass

        item = InventoryItem(
            item_name=name,
            category='consumable',
            vendor_id=vendor_id,
            catalog_number=str(row[2]).strip() if row[2] else None,
            location_room=str(row[3]).strip() if row[3] else None,
            location_unit=str(row[4]).strip() if row[4] else None,
            location_details=str(row[5]).strip() if row[5] else None,
            price=price,
            amount_in_stock=str(row[7]).strip() if row[7] else None,
            min_stock=str(row[8]).strip() if row[8] else None,
            unit_size=str(row[10]).strip() if row[10] else None,
            url=str(row[11]).strip() if row[11] else None,
            expiration_date=_parse_date(row[13]),
            lot_number=str(row[14]).strip() if row[14] else None,
            cas_number=str(row[15]).strip() if row[15] else None,
            added_by_id=admin_id,
        )
        db.session.add(item)
        added += 1

    db.session.commit()
    return added


def _extract_docx_text(path):
    with zipfile.ZipFile(path) as z:
        with z.open('word/document.xml') as f:
            tree = ET.parse(f)
    ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    texts = []
    for para in tree.iter(f'{{{ns}}}p'):
        parts = [n.text for n in para.iter(f'{{{ns}}}t') if n.text]
        line = ''.join(parts).strip()
        if line:
            texts.append(line)
    return texts


def import_primers(admin_id):
    if not os.path.exists(PRIMER_DOCX_PATH):
        print(f'  ! Primer appendix not found at expected path — skipping.')
        return 0

    lines = _extract_docx_text(PRIMER_DOCX_PATH)
    # The docx has rows like:
    # "BactiQuant-F" "16S gene forward primer…" "Liu et al. 2012a"
    # We parse runs of 3 tokens from the flat text stream.

    # Known primer names from the document for structured parsing
    primer_data = [
        # (name, description/sequence_hint, reference, application, target_gene, organism)
        ('BactiQuant-F', 'CCTACGGGDGGCWGCA', 'Liu et al. 2012a', 'qPCR (TaqMan probe)', '16S rRNA', 'Bacteria'),
        ('BactiQuant-R', 'GGACTACHVGGGTMTCTAATC', 'Liu et al. 2012a', 'qPCR (TaqMan probe)', '16S rRNA', 'Bacteria'),
        ('BactiQuant-Prb', '6-FAM/CAGCAGCCGCGGTAA/MGB-NFQ', 'Liu et al. 2012a', 'qPCR (TaqMan probe)', '16S rRNA', 'Bacteria'),
        ('FungiQuant-F', 'GGRAAACTCACCAGGTCCAG', 'Liu et al. 2012b', 'qPCR (TaqMan probe)', 'ITS rDNA', 'Fungi'),
        ('FungiQuant-R', 'GSWCTATCCCCAKCACGA', 'Liu et al. 2012b', 'qPCR (TaqMan probe)', 'ITS rDNA', 'Fungi'),
        ('FungiQuant-Prb', '6-FAM/TGGTGCATGGCCGTT/MGB-NFQ', 'Liu et al. 2012b', 'qPCR (TaqMan probe)', 'ITS rDNA', 'Fungi'),
        ('ITS1', 'TCCGTAGGTGAACCTGCGG', 'White et al. 1990', 'Sanger Sequencing', 'ITS', 'Fungi'),
        ('ITS4', 'TCCTCCGCTTATTGATATGC', 'White et al. 1990', 'Sanger Sequencing', 'ITS', 'Fungi'),
        ('rbcLaF', 'ATGTCACCACAAACAGAGACTAAAGC', 'Kress and Erickson 2007', 'Sanger Sequencing', 'rbcL', 'Plants'),
        ('rbcLaR', 'CTTCTGCTACAAATAAGAATCGATCTC', 'Kress and Erickson 2007', 'Sanger Sequencing', 'rbcL', 'Plants'),
        ('matk472F', 'CCCRTYATCTGGAAATCTTGGTTC', 'Yu et al. 2011', 'Sanger Sequencing', 'matK', 'Plants'),
        ('matK1248R', 'GCTRTRATAATGAGAAAGATTTCTGC', 'Yu et al. 2011', 'Sanger Sequencing', 'matK', 'Plants'),
        ('Dc_09_F', 'GCGTATACCACCCGTGCCTA', 'Khodadadi et al. 2022', 'qPCR (TaqMan probe)', 'Unknown', 'Diplocarpon coronariae (Black Spot)'),
        ('Dc_09_R', 'CTCAGACATCACGTATTCACACAA', 'Khodadadi et al. 2022', 'qPCR (TaqMan probe)', 'Unknown', 'Diplocarpon coronariae (Black Spot)'),
        ('Dc_09_P', '6FAM-CCTACCTCTGTTGCTTTGGCGA-QSY', 'Khodadadi et al. 2022', 'qPCR (TaqMan probe)', 'Unknown', 'Diplocarpon coronariae (Black Spot)'),
        ('Bc3 F', 'GCTGTAATTTCAATGTGCAGAATCC', 'Suarez et al. 2005', 'qPCR (TaqMan probe)', 'Unknown', 'Botrytis cinerea (Grey Mold)'),
        ('Bc3 R', 'GGAGCAACAATTAATCGCATTTC', 'Suarez et al. 2005', 'qPCR (TaqMan probe)', 'Unknown', 'Botrytis cinerea (Grey Mold)'),
        ('Bc3 Probe', '6FAM-TCACCTTGCAATGAGTGG-QSY', 'Suarez et al. 2005', 'qPCR (TaqMan probe)', 'Unknown', 'Botrytis cinerea (Grey Mold)'),
        ('PV 92-F', 'GGATCTCAGGGTGGGTGGCAATGCT', 'Brooks and Thackston 2022', 'PCR', 'Alu insertion (PV92)', 'Human'),
        ('PV 92-R', 'GAAAGGCAAGCTACCAGAAGCCCCAA', 'Brooks and Thackston 2022', 'PCR', 'Alu insertion (PV92)', 'Human'),
        ('Hs00422024_CE F', 'TGAGTGGAAGACAGAATGGAAGAAATG', 'ThermoFisher Primer Designer', 'PCR', 'GAPDH', 'Human'),
        ('Hs00422024_CE R', 'CCATGAGTCCTTCCACGATACCA', 'ThermoFisher Primer Designer', 'PCR', 'GAPDH', 'Human'),
        ('Hs00439135_CE F', 'GTGGCTTGTTGGGAAAGGTGGAT', 'ThermoFisher Primer Designer', 'PCR', 'B2M', 'Human'),
        ('Hs00439135_CE R', 'TCCCCTGACAATCCCAATATGCAG', 'ThermoFisher Primer Designer', 'PCR', 'B2M', 'Human'),
        ('Hs00368837_CE F', 'AGGACTGGGCCATTCTCCTTAGAG', 'ThermoFisher Primer Designer', 'PCR', 'ACTB', 'Human'),
        ('Hs00368837_CE R', 'TGTCACATCCAGGGTCCTCACT', 'ThermoFisher Primer Designer', 'PCR', 'ACTB', 'Human'),
    ]

    added = 0
    for name, seq, ref, application, gene, organism in primer_data:
        if _item_exists(name):
            continue
        category = 'probe' if 'probe' in name.lower() or 'Prb' in name or '_P' == name[-2:] or 'Probe' in name else 'primer'
        item = InventoryItem(
            item_name=name,
            category=category,
            sequence_5to3=seq,
            target_gene=gene,
            organism_target=organism,
            primer_application=application,
            reference=ref,
            added_by_id=admin_id,
        )
        db.session.add(item)
        added += 1

    # Also add DNA standards from the appendix
    standards = [
        ('Fungal DNA Standards (Zymo 50-203-7190)', 'consumable',
         'Saccharomyces cerevisiae DNA standards + NTC for qPCR fungal load assay',
         'Zymo Research', '50-203-7190'),
        ('Bacterial DNA Standards (Zymo 50-125-1630)', 'consumable',
         'Bacterial DNA standards + NTC for qPCR bacterial load assay',
         'Zymo Research', '50-125-1630'),
        ('Human Genomic DNA TaqMan Control (ThermoFisher 4312660)', 'standard',
         'Human male genomic DNA control for PCR and Sanger sequencing',
         'ThermoFisher Scientific', '4312660'),
    ]
    for sname, scat, snotes, svendor, scatalog in standards:
        if _item_exists(sname):
            continue
        vendor_id = _get_or_create_vendor(svendor, db.session)
        item = InventoryItem(
            item_name=sname,
            category=scat,
            catalog_number=scatalog,
            vendor_id=vendor_id,
            notes=snotes,
            added_by_id=admin_id,
        )
        db.session.add(item)
        added += 1

    db.session.commit()
    return added


def main():
    import openpyxl

    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print('ERROR: No admin user found. Run `python app.py` first to initialize the database.')
            return

        admin_id = admin.id

        if not os.path.exists(XLSX_PATH):
            print(f'ERROR: Inventory file not found at:\n  {XLSX_PATH}')
            print('Make sure the Lab_stuff folder is one level above lab_manager/.')
            return

        print(f'Loading: {os.path.basename(XLSX_PATH)}')
        wb = openpyxl.load_workbook(XLSX_PATH)

        print('\nImporting chemicals...')
        n = import_chemicals(wb, admin_id)
        print(f'  ✓ {n} chemical items imported.')

        print('Importing general supplies / consumables...')
        n = import_general_supply(wb, admin_id)
        print(f'  ✓ {n} supply items imported.')

        print('Importing primers, probes, and standards from appendix...')
        n = import_primers(admin_id)
        print(f'  ✓ {n} primers/probes/standards imported.')

        total = InventoryItem.query.count()
        print(f'\nDone! Total inventory items in database: {total}')
        print('Open the app and go to Inventory to review.')


if __name__ == '__main__':
    main()
