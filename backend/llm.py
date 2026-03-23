"""LLM utilities for translating questions into SQL and summarizing results."""

from __future__ import annotations

import os
from typing import Dict, List

from dotenv import load_dotenv
from groq import Groq

from database import run_query

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


KNOWN_QUERIES = {
    "highest number of billing documents": (
        "SELECT bdi.material, COUNT(DISTINCT bdi.billingDocument) as num_billing_documents "
        "FROM billing_document_items bdi "
        "GROUP BY bdi.material ORDER BY num_billing_documents DESC LIMIT 1"
    ),
    "delivered but not billed": (
        "SELECT DISTINCT odi.salesOrder FROM outbound_delivery_items odi "
        "LEFT JOIN billing_document_items bdi "
        "ON odi.salesOrder = bdi.salesOrder AND odi.salesOrderItem = bdi.salesOrderItem "
        "WHERE bdi.billingDocument IS NULL"
    ),
    "billed without delivery": (
        "SELECT DISTINCT bdi.salesOrder FROM billing_document_items bdi "
        "LEFT JOIN outbound_delivery_items odi "
        "ON bdi.salesOrder = odi.salesOrder AND bdi.salesOrderItem = odi.salesOrderItem "
        "WHERE odi.deliveryDocument IS NULL"
    ),
}


def match_known_query(message: str):
    lower = message.lower()
    for keyword, sql in KNOWN_QUERIES.items():
        if keyword in lower:
            return sql
    return None


def _format_results(results: List[Dict]) -> str:
    if not results:
        return "No matching records were found."

    if len(results) == 1 and len(results[0]) == 1:
        value = next(iter(results[0].values()))
        return f"The answer is {value}."

    lines = [f"Found {len(results)} matching record(s):"]
    for row in results:
        parts = []
        for key, value in row.items():
            parts.append(f"{key}: {value}")
        lines.append("- " + ", ".join(parts))
    return "\n".join(lines)


def ask(message: str) -> str:
    known_sql = match_known_query(message)
    if known_sql:
        try:
            results = run_query(known_sql)
        except Exception as e:
            print(f"Error: {e}")
            return "Something went wrong, please try again."
        return _format_results(results)

    system_instruction = (
        "You are a data analyst assistant for a SAP Order to Cash dataset. "
        "You have access to these SQLite tables and their columns:\n"
        "sales_order_headers: salesOrder, salesOrderType, soldToParty, creationDate, "
        "totalNetAmount, overallDeliveryStatus, transactionCurrency\n"
        "sales_order_items: salesOrder, salesOrderItem, material, requestedQuantity, "
        "netAmount, productionPlant, storageLocation\n"
        "billing_document_headers: billingDocument, billingDocumentType, creationDate, "
        "totalNetAmount, soldToParty, accountingDocument, fiscalYear, companyCode, "
        "billingDocumentIsCancelled\n"
        "billing_document_items: billingDocument, billingDocumentItem, salesOrder, "
        "salesOrderItem, material, billingQuantity, netAmount\n"
        "outbound_delivery_headers: deliveryDocument, creationDate, shippingPoint, "
        "overallGoodsMovementStatus, overallPickingStatus\n"
        "outbound_delivery_items: deliveryDocument, deliveryDocumentItem, salesOrder, "
        "salesOrderItem, material, actualDeliveryQuantity\n"
        "payments_accounts_receivable: accountingDocument, accountingDocumentItem, "
        "customer, amountInTransactionCurrency, transactionCurrency, postingDate, "
        "clearingDate, clearingAccountingDocument\n"
        "journal_entry_items_accounts_receivable: accountingDocument, accountingDocumentItem, "
        "referenceDocument, glAccount, amountInTransactionCurrency, transactionCurrency, "
        "postingDate, customer, accountingDocumentType\n"
        "business_partners: businessPartner, businessPartnerFullName, businessPartnerType\n"
        "products: material, baseUnit, materialType, materialGroup\n"
        "Important query writing rules:\n"
        "- To find products with the most billing documents, JOIN billing_document_items "
        "with products on material and COUNT with GROUP BY material ORDER BY count DESC LIMIT 1\n"
        "- To trace a billing document flow, JOIN billing_document_headers with "
        "billing_document_items on billingDocument, LEFT JOIN outbound_delivery_items on "
        "salesOrder and salesOrderItem, LEFT JOIN journal_entry_items_accounts_receivable "
        "on accountingDocument, LEFT JOIN payments_accounts_receivable on accountingDocument\n"
        "- To find sales orders delivered but not billed, LEFT JOIN outbound_delivery_items "
        "and billing_document_items on salesOrder and salesOrderItem WHERE "
        "billing_document_items.billingDocument IS NULL\n"
        "- Always use CAST for numeric comparisons on amount fields\n"
        "- Never use table aliases that conflict with column names\n"
        "Here are example question and SQL pairs to guide your query generation:\n"
        "\n"
        "Q: Which products are associated with the highest number of billing documents?\n"
        "A: SELECT bdi.material, COUNT(DISTINCT bdi.billingDocument) as num_billing_documents FROM billing_document_items bdi GROUP BY bdi.material ORDER BY num_billing_documents DESC LIMIT 1\n"
        "\n"
        "Q: Which customer has the highest total payment amount?\n"
        "A: SELECT customer, SUM(CAST(amountInTransactionCurrency AS REAL)) as total_amount FROM payments_accounts_receivable GROUP BY customer ORDER BY total_amount DESC LIMIT 1\n"
        "\n"
        "Q: How many sales orders are there in total?\n"
        "A: SELECT COUNT(DISTINCT salesOrder) as total FROM sales_order_headers\n"
        "\n"
        "Q: Identify sales orders delivered but not billed?\n"
        "A: SELECT DISTINCT odi.salesOrder FROM outbound_delivery_items odi LEFT JOIN billing_document_items bdi ON odi.salesOrder = bdi.salesOrder AND odi.salesOrderItem = bdi.salesOrderItem WHERE bdi.billingDocument IS NULL\n"
        "\n"
        "Q: Which billing document has the highest total net amount?\n"
        "A: SELECT billingDocument, totalNetAmount FROM billing_document_headers ORDER BY CAST(totalNetAmount AS REAL) DESC LIMIT 1\n"
        "\n"
        "Use these as reference patterns when generating SQL for similar questions.\n"
        "When the user asks a question write a valid SQLite SQL query to answer it. "
        "Return only the raw SQL query with no explanation, no markdown formatting, "
        "and no backticks. If the question is unrelated to this dataset or business data "
        "return exactly this and nothing else: OFFTOPIC"
    )

    prompt = (
        "Table schema:\n"
        "sales_order_headers: salesOrder, salesOrderType, soldToParty, creationDate, "
        "totalNetAmount, overallDeliveryStatus, transactionCurrency\n"
        "sales_order_items: salesOrder, salesOrderItem, material, requestedQuantity, "
        "netAmount, productionPlant, storageLocation\n"
        "billing_document_headers: billingDocument, billingDocumentType, creationDate, "
        "totalNetAmount, soldToParty, accountingDocument, fiscalYear, companyCode, "
        "billingDocumentIsCancelled\n"
        "billing_document_items: billingDocument, billingDocumentItem, salesOrder, "
        "salesOrderItem, material, billingQuantity, netAmount\n"
        "outbound_delivery_headers: deliveryDocument, creationDate, shippingPoint, "
        "overallGoodsMovementStatus, overallPickingStatus\n"
        "outbound_delivery_items: deliveryDocument, deliveryDocumentItem, salesOrder, "
        "salesOrderItem, material, actualDeliveryQuantity\n"
        "payments_accounts_receivable: accountingDocument, accountingDocumentItem, "
        "customer, amountInTransactionCurrency, transactionCurrency, postingDate, "
        "clearingDate, clearingAccountingDocument\n"
        "journal_entry_items_accounts_receivable: accountingDocument, accountingDocumentItem, "
        "referenceDocument, glAccount, amountInTransactionCurrency, transactionCurrency, "
        "postingDate, customer, accountingDocumentType\n"
        "business_partners: businessPartner, businessPartnerFullName, businessPartnerType\n"
        "products: material, baseUnit, materialType, materialGroup\n\n"
        f"User question: {message}"
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
        )
        sql = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: {e}")
        return "Something went wrong, please try again."

    if sql == "OFFTOPIC":
        return "OFFTOPIC"

    if not sql:
        return "Something went wrong, please try again."

    print(f"SQL from Groq: {sql}")

    try:
        results = run_query(sql)
    except Exception as e:
        print(f"Error: {e}")
        return "Something went wrong, please try again."

    return _format_results(results)
