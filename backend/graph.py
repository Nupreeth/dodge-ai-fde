"""Graph construction utilities for the SAP Order to Cash dataset."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import networkx as nx

from database import run_query

GraphType = nx.DiGraph

GRAPH: Optional[GraphType] = None


def _normalize_key(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return str(value)


def _compose_id(prefix: str, *parts: Optional[str]) -> Optional[str]:
    normalized = [_normalize_key(part) for part in parts]
    if any(part is None for part in normalized):
        return None
    return f"{prefix}_" + "_".join(normalized)


def _add_node(graph: GraphType, node_id: Optional[str], node_type: str, data: Dict) -> None:
    if node_id is None:
        return
    graph.add_node(node_id, type=node_type, data=data)


def build_graph() -> None:
    global GRAPH

    graph: GraphType = nx.DiGraph()

    sales_order_headers = run_query("SELECT * FROM sales_order_headers")
    sales_order_items = run_query("SELECT * FROM sales_order_items")
    billing_document_headers = run_query("SELECT * FROM billing_document_headers")
    billing_document_items = run_query("SELECT * FROM billing_document_items")
    outbound_delivery_headers = run_query("SELECT * FROM outbound_delivery_headers")
    outbound_delivery_items = run_query("SELECT * FROM outbound_delivery_items")
    payments_accounts_receivable = run_query("SELECT * FROM payments_accounts_receivable")
    journal_entry_items_accounts_receivable = run_query(
        "SELECT * FROM journal_entry_items_accounts_receivable"
    )
    business_partners = run_query("SELECT * FROM business_partners")
    products = run_query("SELECT * FROM products")

    sales_order_header_ids: Dict[str, str] = {}
    sales_order_item_ids: Dict[Tuple[str, str], str] = {}
    billing_document_header_ids: Dict[str, str] = {}
    billing_document_item_ids: Dict[Tuple[str, str], str] = {}
    outbound_delivery_header_ids: Dict[str, str] = {}
    outbound_delivery_item_ids: Dict[Tuple[str, str], str] = {}
    payment_ids: Dict[Tuple[str, str], str] = {}
    journal_entry_item_ids: Dict[Tuple[str, str], str] = {}
    business_partner_ids: Dict[str, str] = {}
    product_ids: Dict[str, str] = {}

    accounting_doc_to_billing_header_ids: Dict[str, List[str]] = {}

    for row in sales_order_headers:
        key = _normalize_key(row.get("salesOrder"))
        node_id = _compose_id("sales_order", key)
        _add_node(graph, node_id, "sales_order_header", row)
        if key and node_id:
            sales_order_header_ids[key] = node_id

    for row in sales_order_items:
        order = _normalize_key(row.get("salesOrder"))
        item = _normalize_key(row.get("salesOrderItem"))
        node_id = _compose_id("sales_order_item", order, item)
        _add_node(graph, node_id, "sales_order_item", row)
        if order and item and node_id:
            sales_order_item_ids[(order, item)] = node_id

    for row in billing_document_headers:
        key = _normalize_key(row.get("billingDocument"))
        node_id = _compose_id("billing_document", key)
        _add_node(graph, node_id, "billing_document_header", row)
        if key and node_id:
            billing_document_header_ids[key] = node_id
        accounting_doc = _normalize_key(row.get("accountingDocument"))
        if accounting_doc and node_id:
            accounting_doc_to_billing_header_ids.setdefault(accounting_doc, []).append(node_id)

    for row in billing_document_items:
        doc = _normalize_key(row.get("billingDocument"))
        item = _normalize_key(row.get("billingDocumentItem"))
        node_id = _compose_id("billing_document_item", doc, item)
        _add_node(graph, node_id, "billing_document_item", row)
        if doc and item and node_id:
            billing_document_item_ids[(doc, item)] = node_id

    for row in outbound_delivery_headers:
        key = _normalize_key(row.get("deliveryDocument"))
        node_id = _compose_id("outbound_delivery", key)
        _add_node(graph, node_id, "outbound_delivery_header", row)
        if key and node_id:
            outbound_delivery_header_ids[key] = node_id

    for row in outbound_delivery_items:
        doc = _normalize_key(row.get("deliveryDocument"))
        item = _normalize_key(row.get("deliveryDocumentItem"))
        node_id = _compose_id("outbound_delivery_item", doc, item)
        _add_node(graph, node_id, "outbound_delivery_item", row)
        if doc and item and node_id:
            outbound_delivery_item_ids[(doc, item)] = node_id

    for row in payments_accounts_receivable:
        doc = _normalize_key(row.get("accountingDocument"))
        item = _normalize_key(row.get("accountingDocumentItem"))
        node_id = _compose_id("payment", doc, item)
        _add_node(graph, node_id, "payment", row)
        if doc and item and node_id:
            payment_ids[(doc, item)] = node_id

    for row in journal_entry_items_accounts_receivable:
        doc = _normalize_key(row.get("accountingDocument"))
        item = _normalize_key(row.get("accountingDocumentItem"))
        node_id = _compose_id("journal_entry_item", doc, item)
        _add_node(graph, node_id, "journal_entry_item", row)
        if doc and item and node_id:
            journal_entry_item_ids[(doc, item)] = node_id

    for row in business_partners:
        key = _normalize_key(row.get("businessPartner"))
        node_id = _compose_id("business_partner", key)
        _add_node(graph, node_id, "business_partner", row)
        if key and node_id:
            business_partner_ids[key] = node_id

    for row in products:
        key = _normalize_key(row.get("material"))
        node_id = _compose_id("product", key)
        _add_node(graph, node_id, "product", row)
        if key and node_id:
            product_ids[key] = node_id

    for row in sales_order_items:
        order = _normalize_key(row.get("salesOrder"))
        item = _normalize_key(row.get("salesOrderItem"))
        header_id = sales_order_header_ids.get(order or "")
        item_id = sales_order_item_ids.get((order or "", item or ""))
        if header_id and item_id:
            graph.add_edge(header_id, item_id)

        material = _normalize_key(row.get("material"))
        product_id = product_ids.get(material or "")
        if item_id and product_id:
            graph.add_edge(item_id, product_id)

    for row in billing_document_items:
        doc = _normalize_key(row.get("billingDocument"))
        item = _normalize_key(row.get("billingDocumentItem"))
        billing_item_id = billing_document_item_ids.get((doc or "", item or ""))

        order = _normalize_key(row.get("salesOrder"))
        order_item = _normalize_key(row.get("salesOrderItem"))
        sales_item_id = sales_order_item_ids.get((order or "", order_item or ""))
        if billing_item_id and sales_item_id:
            graph.add_edge(billing_item_id, sales_item_id)

    for row in outbound_delivery_items:
        doc = _normalize_key(row.get("deliveryDocument"))
        item = _normalize_key(row.get("deliveryDocumentItem"))
        delivery_item_id = outbound_delivery_item_ids.get((doc or "", item or ""))

        order = _normalize_key(row.get("salesOrder"))
        order_item = _normalize_key(row.get("salesOrderItem"))
        sales_item_id = sales_order_item_ids.get((order or "", order_item or ""))
        if delivery_item_id and sales_item_id:
            graph.add_edge(delivery_item_id, sales_item_id)

    for row in journal_entry_items_accounts_receivable:
        doc = _normalize_key(row.get("accountingDocument"))
        item = _normalize_key(row.get("accountingDocumentItem"))
        journal_id = journal_entry_item_ids.get((doc or "", item or ""))
        if not journal_id:
            continue
        for billing_id in accounting_doc_to_billing_header_ids.get(doc or "", []):
            graph.add_edge(billing_id, journal_id)

    for row in payments_accounts_receivable:
        doc = _normalize_key(row.get("accountingDocument"))
        item = _normalize_key(row.get("accountingDocumentItem"))
        payment_id = payment_ids.get((doc or "", item or ""))
        partner_key = _normalize_key(row.get("customer"))
        partner_id = business_partner_ids.get(partner_key or "")
        if payment_id and partner_id:
            graph.add_edge(payment_id, partner_id)

    for row in billing_document_headers:
        key = _normalize_key(row.get("billingDocument"))
        header_id = billing_document_header_ids.get(key or "")
        partner_key = _normalize_key(row.get("soldToParty"))
        partner_id = business_partner_ids.get(partner_key or "")
        if header_id and partner_id:
            graph.add_edge(header_id, partner_id)

    for row in sales_order_headers:
        key = _normalize_key(row.get("salesOrder"))
        header_id = sales_order_header_ids.get(key or "")
        partner_key = _normalize_key(row.get("soldToParty"))
        partner_id = business_partner_ids.get(partner_key or "")
        if header_id and partner_id:
            graph.add_edge(header_id, partner_id)

    GRAPH = graph


def _ensure_graph() -> GraphType:
    global GRAPH
    if GRAPH is None:
        build_graph()
    return GRAPH


def get_graph() -> Dict[str, List[Dict]]:
    graph = _ensure_graph()
    nodes = []
    for node_id, attrs in graph.nodes(data=True):
        nodes.append(
            {
                "id": node_id,
                "type": attrs.get("type"),
                "data": attrs.get("data", {}),
            }
        )

    edges = []
    for source, target in graph.edges():
        edges.append({"source": source, "target": target})

    return {"nodes": nodes, "edges": edges}


def get_neighbors(node_id: str) -> List[Dict]:
    graph = _ensure_graph()
    if node_id not in graph:
        return []

    neighbor_ids = set(graph.successors(node_id)) | set(graph.predecessors(node_id))
    neighbors = []
    for neighbor_id in neighbor_ids:
        attrs = graph.nodes[neighbor_id]
        neighbors.append(
            {
                "id": neighbor_id,
                "type": attrs.get("type"),
                "data": attrs.get("data", {}),
            }
        )
    return neighbors
