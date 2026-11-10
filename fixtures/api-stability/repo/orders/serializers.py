"""Turn Order objects into v1 response bodies."""


def _money(minor):
    return str(minor)


def item_v1(item):
    return {
        "sku": item.sku,
        "qty": item.qty,
        "unit_amt": _money(item.unit_amt),
    }


def order_v1(order):
    return {
        "id": order.oid,
        "cust_nm": order.cust_nm,
        "cust_email": order.cust_email,
        "amt": _money(order.amt),
        "status": order.status,
        "items": [item_v1(i) for i in order.items],
        "note": order.note,
        "created_ts": order.created_ts,
    }


def order_list_v1(orders):
    return {
        "data": [order_v1(o) for o in orders],
        "count": len(orders),
    }
