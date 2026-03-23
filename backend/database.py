"""SQLite database utilities for the SAP Order to Cash dataset."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "o2c.db"

# Core table schemas explicitly defined by the project requirements.
CORE_TABLE_SCHEMAS: Dict[str, List[str]] = {
    "sales_order_headers": [
        "salesOrder",
        "salesOrderType",
        "soldToParty",
        "creationDate",
        "totalNetAmount",
        "overallDeliveryStatus",
        "transactionCurrency",
    ],
    "sales_order_items": [
        "salesOrder",
        "salesOrderItem",
        "material",
        "requestedQuantity",
        "netAmount",
        "productionPlant",
        "storageLocation",
    ],
    "billing_document_headers": [
        "billingDocument",
        "billingDocumentType",
        "creationDate",
        "totalNetAmount",
        "soldToParty",
        "accountingDocument",
        "fiscalYear",
        "companyCode",
        "billingDocumentIsCancelled",
    ],
    "billing_document_items": [
        "billingDocument",
        "billingDocumentItem",
        "salesOrder",
        "salesOrderItem",
        "material",
        "billingQuantity",
        "netAmount",
    ],
    "outbound_delivery_headers": [
        "deliveryDocument",
        "creationDate",
        "shippingPoint",
        "overallGoodsMovementStatus",
        "overallPickingStatus",
    ],
    "outbound_delivery_items": [
        "deliveryDocument",
        "deliveryDocumentItem",
        "salesOrder",
        "salesOrderItem",
        "material",
        "actualDeliveryQuantity",
    ],
    "payments_accounts_receivable": [
        "accountingDocument",
        "accountingDocumentItem",
        "customer",
        "amountInTransactionCurrency",
        "transactionCurrency",
        "postingDate",
        "clearingDate",
        "clearingAccountingDocument",
    ],
    "journal_entry_items_accounts_receivable": [
        "accountingDocument",
        "accountingDocumentItem",
        "referenceDocument",
        "glAccount",
        "amountInTransactionCurrency",
        "transactionCurrency",
        "postingDate",
        "customer",
        "accountingDocumentType",
    ],
    "business_partners": [
        "businessPartner",
        "businessPartnerFullName",
        "businessPartnerType",
    ],
    "products": [
        "material",
        "baseUnit",
        "materialType",
        "materialGroup",
    ],
}

# Non-core tables: schemas derived from the dataset keys for completeness.
EXTRA_TABLE_SCHEMAS: Dict[str, List[str]] = {
    "billing_document_cancellations": [
        "accountingDocument",
        "billingDocument",
        "billingDocumentDate",
        "billingDocumentIsCancelled",
        "billingDocumentType",
        "cancelledBillingDocument",
        "companyCode",
        "creationDate",
        "creationTime",
        "fiscalYear",
        "lastChangeDateTime",
        "soldToParty",
        "totalNetAmount",
        "transactionCurrency",
    ],
    "business_partner_addresses": [
        "addressId",
        "addressTimeZone",
        "addressUuid",
        "businessPartner",
        "cityName",
        "country",
        "poBox",
        "poBoxDeviatingCityName",
        "poBoxDeviatingCountry",
        "poBoxDeviatingRegion",
        "poBoxIsWithoutNumber",
        "poBoxLobbyName",
        "poBoxPostalCode",
        "postalCode",
        "region",
        "streetName",
        "taxJurisdiction",
        "transportZone",
        "validityEndDate",
        "validityStartDate",
    ],
    "customer_company_assignments": [
        "accountingClerk",
        "accountingClerkFaxNumber",
        "accountingClerkInternetAddress",
        "accountingClerkPhoneNumber",
        "alternativePayerAccount",
        "companyCode",
        "customer",
        "customerAccountGroup",
        "deletionIndicator",
        "paymentBlockingReason",
        "paymentMethodsList",
        "paymentTerms",
        "reconciliationAccount",
    ],
    "customer_sales_area_assignments": [
        "billingIsBlockedForCustomer",
        "completeDeliveryIsDefined",
        "creditControlArea",
        "currency",
        "customer",
        "customerPaymentTerms",
        "deliveryPriority",
        "distributionChannel",
        "division",
        "exchangeRateType",
        "incotermsClassification",
        "incotermsLocation1",
        "salesDistrict",
        "salesGroup",
        "salesOffice",
        "salesOrganization",
        "shippingCondition",
        "slsUnlmtdOvrdelivIsAllwd",
        "supplyingPlant",
    ],
    "plants": [
        "addressId",
        "defaultPurchasingOrganization",
        "distributionChannel",
        "division",
        "factoryCalendar",
        "isMarkedForArchiving",
        "language",
        "plant",
        "plantCategory",
        "plantCustomer",
        "plantName",
        "plantSupplier",
        "salesOrganization",
        "valuationArea",
    ],
    "product_descriptions": [
        "language",
        "product",
        "productDescription",
    ],
    "product_plants": [
        "availabilityCheckType",
        "countryOfOrigin",
        "fiscalYearVariant",
        "mrpType",
        "plant",
        "product",
        "productionInvtryManagedLoc",
        "profitCenter",
        "regionOfOrigin",
    ],
    "product_storage_locations": [
        "dateOfLastPostedCntUnRstrcdStk",
        "physicalInventoryBlockInd",
        "plant",
        "product",
        "storageLocation",
    ],
    "sales_order_schedule_lines": [
        "confdOrderQtyByMatlAvailCheck",
        "confirmedDeliveryDate",
        "orderQuantityUnit",
        "salesOrder",
        "salesOrderItem",
        "scheduleLine",
    ],
}

ALL_TABLES: List[str] = [
    "sales_order_headers",
    "sales_order_items",
    "billing_document_headers",
    "billing_document_items",
    "billing_document_cancellations",
    "outbound_delivery_headers",
    "outbound_delivery_items",
    "payments_accounts_receivable",
    "journal_entry_items_accounts_receivable",
    "business_partners",
    "business_partner_addresses",
    "products",
    "product_descriptions",
    "product_plants",
    "product_storage_locations",
    "plants",
    "customer_company_assignments",
    "customer_sales_area_assignments",
    "sales_order_schedule_lines",
]


def _resolve_dataset_dir() -> Path:
    root_dir = BASE_DIR.parent
    candidates = [
        root_dir / "sap-o2c-data",
        root_dir / "sap-order-to-cash-dataset" / "sap-o2c-data",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _infer_schema(table_name: str, dataset_dir: Path) -> List[str]:
    folder = dataset_dir / table_name
    if not folder.exists():
        return []
    keys = set()
    for file_path in folder.glob("*.jsonl"):
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    keys.update(obj.keys())
        except Exception:
            continue
    return sorted(keys)


def _create_tables(conn: sqlite3.Connection, dataset_dir: Path) -> None:
    for table_name in ALL_TABLES:
        columns = CORE_TABLE_SCHEMAS.get(table_name)
        if columns is None:
            columns = EXTRA_TABLE_SCHEMAS.get(table_name)
        if not columns:
            columns = _infer_schema(table_name, dataset_dir) or ["raw_json"]
        column_defs = ", ".join([f'"{col}" TEXT' for col in columns])
        conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({column_defs})')
    conn.commit()


def _extract_with_fallback(record: dict, keys: Iterable[str]) -> Optional[str]:
    for key in keys:
        value = record.get(key)
        if value is not None:
            return value
    return None


def _build_core_row(table_name: str, record: dict) -> List[Optional[str]]:
    schema = CORE_TABLE_SCHEMAS[table_name]

    if table_name == "billing_document_items":
        mapping = {
            "salesOrder": ["salesOrder", "referenceSdDocument"],
            "salesOrderItem": ["salesOrderItem", "referenceSdDocumentItem"],
        }
        return [
            _extract_with_fallback(record, mapping.get(col, [col]))
            for col in schema
        ]

    if table_name == "outbound_delivery_items":
        mapping = {
            "salesOrder": ["salesOrder", "referenceSdDocument"],
            "salesOrderItem": ["salesOrderItem", "referenceSdDocumentItem"],
        }
        return [
            _extract_with_fallback(record, mapping.get(col, [col]))
            for col in schema
        ]

    if table_name == "products":
        mapping = {
            "material": ["material", "product"],
            "materialType": ["materialType", "productType"],
            "materialGroup": ["materialGroup", "productGroup"],
        }
        return [
            _extract_with_fallback(record, mapping.get(col, [col]))
            for col in schema
        ]

    if table_name == "business_partners":
        mapping = {
            "businessPartnerType": ["businessPartnerType", "businessPartnerCategory"],
        }
        return [
            _extract_with_fallback(record, mapping.get(col, [col]))
            for col in schema
        ]

    return [record.get(col) for col in schema]


def _insert_record(
    conn: sqlite3.Connection, table_name: str, columns: List[str], values: List[Optional[str]]
) -> None:
    placeholders = ", ".join(["?"] * len(columns))
    column_list = ", ".join([f'"{col}"' for col in columns])
    sql = f'INSERT INTO "{table_name}" ({column_list}) VALUES ({placeholders})'
    try:
        conn.execute(sql, values)
    except Exception:
        return


def load_all_data() -> None:
    dataset_dir = _resolve_dataset_dir()
    conn = _get_connection()
    _create_tables(conn, dataset_dir)

    for table_name in ALL_TABLES:
        try:
            conn.execute(f'DELETE FROM "{table_name}"')
        except Exception:
            continue
    conn.commit()

    for table_name in ALL_TABLES:
        folder = dataset_dir / table_name
        if not folder.exists():
            continue

        columns = CORE_TABLE_SCHEMAS.get(table_name) or EXTRA_TABLE_SCHEMAS.get(table_name)
        if not columns:
            columns = _infer_schema(table_name, dataset_dir) or ["raw_json"]

        for file_path in sorted(folder.glob("*.jsonl")):
            try:
                with file_path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                        except Exception:
                            continue

                        if columns == ["raw_json"]:
                            values = [json.dumps(record)]
                        elif table_name in CORE_TABLE_SCHEMAS:
                            values = _build_core_row(table_name, record)
                        else:
                            values = [record.get(col) for col in columns]

                        _insert_record(conn, table_name, columns, values)
            except Exception:
                continue

    conn.commit()
    conn.close()


def run_query(sql: str) -> List[Dict[str, Optional[str]]]:
    conn = _get_connection()
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        return results
    finally:
        conn.close()
