from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

@dataclass
class LineItem:
    sku: str
    category: str
    unit_price: float
    qty: int
    fragile: bool = False

@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    country: str
    membership: str
    coupon: Optional[str]
    items: List[LineItem]

    
class InvoiceService:
    def __init__(self) -> None:
        self._coupon_rate: Dict[str, float] = {
            "WELCOME10": 0.10,
            "VIP20": 0.20,
            "STUDENT5": 0.05
        }

    # ...existing code...

    def _calculate_shipping(self, country: str, subtotal: float) -> float:
        """Calculate shipping based on country and subtotal."""
        shipping_rules = {
            "TH": [(500, 60), (float('inf'), 0)],
            "JP": [(4000, 600), (float('inf'), 0)],
            "US": [(100, 15), (300, 8), (float('inf'), 0)],
        }
        
        rules = shipping_rules.get(country, [(200, 25), (float('inf'), 0)])
        for threshold, cost in rules:
            if subtotal < threshold:
                return cost
        return 0.0

    def _calculate_discount(self, inv: Invoice, subtotal: float, warnings: List[str]) -> float:
        """Calculate discount from membership and coupon."""
        discount = 0.0
        
        if inv.membership == "gold":
            discount += subtotal * 0.03
        elif inv.membership == "platinum":
            discount += subtotal * 0.05
        else:
            if subtotal > 3000:
                discount += 20
        
        if inv.coupon is not None and inv.coupon.strip() != "":
            code = inv.coupon.strip()
            if code in self._coupon_rate:
                discount += subtotal * self._coupon_rate[code]
            else:
                warnings.append("Unknown coupon")
        
        return discount

    def _calculate_tax(self, country: str, taxable_amount: float) -> float:
        """Calculate tax based on country."""
        tax_rates = {
            "TH": 0.07,
            "JP": 0.10,
            "US": 0.08,
        }
        rate = tax_rates.get(country, 0.05)
        return taxable_amount * rate

    def compute_total(self, inv: Invoice) -> Tuple[float, List[str]]:
        warnings: List[str] = []
        problems = self._validate(inv)
        if problems:
            raise ValueError("; ".join(problems))

        subtotal = sum(it.unit_price * it.qty for it in inv.items)
        fragile_fee = sum(5.0 * it.qty for it in inv.items if it.fragile)
        
        shipping = self._calculate_shipping(inv.country, subtotal)
        discount = self._calculate_discount(inv, subtotal, warnings)
        tax = self._calculate_tax(inv.country, subtotal - discount)

        total = subtotal + shipping + fragile_fee + tax - discount
        total = max(0, total)

        if subtotal > 10000 and inv.membership not in ("gold", "platinum"):
            warnings.append("Consider membership upgrade")

        return total, warnings