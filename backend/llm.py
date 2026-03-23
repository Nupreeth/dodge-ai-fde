"""LLM utilities for translating questions into SQL and summarizing results."""

from __future__ import annotations

import os
from typing import Dict, List

from dotenv import load_dotenv
from groq import Groq

from database import run_query

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


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
