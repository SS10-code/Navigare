/**
 * Client-side inventory health analysis for guest users.
 * Computes stock health metrics without backend access.
 */

export interface InventoryItem {
  sku: string;
  name?: string;
  currentStock: number;
  reorderPoint: number;
  maxStock: number;
  unitCost?: number;
}

export interface InventoryHealthReport {
  totalItems: number;
  healthy: number;
  atRisk: number;
  outOfStock: number;
  overstocked: number;
  totalValue: number;
  healthScore: number; // 0-100
  items: Array<InventoryItem & { status: "healthy" | "at_risk" | "out_of_stock" | "overstocked" }>;
}

export function analyzeInventoryHealth(items: InventoryItem[]): InventoryHealthReport {
  if (!items.length) {
    return {
      totalItems: 0,
      healthy: 0,
      atRisk: 0,
      outOfStock: 0,
      overstocked: 0,
      totalValue: 0,
      healthScore: 0,
      items: [],
    };
  }

  let healthy = 0;
  let atRisk = 0;
  let outOfStock = 0;
  let overstocked = 0;
  let totalValue = 0;

  const analyzedItems = items.map((item) => {
    const value = item.currentStock * (item.unitCost || 0);
    totalValue += value;

    let status: "healthy" | "at_risk" | "out_of_stock" | "overstocked";
    if (item.currentStock <= 0) {
      status = "out_of_stock";
      outOfStock++;
    } else if (item.currentStock <= item.reorderPoint) {
      status = "at_risk";
      atRisk++;
    } else if (item.currentStock >= item.maxStock) {
      status = "overstocked";
      overstocked++;
    } else {
      status = "healthy";
      healthy++;
    }

    return { ...item, status };
  });

  const healthScore = Math.round(((healthy + atRisk * 0.5) / items.length) * 100);

  return {
    totalItems: items.length,
    healthy,
    atRisk,
    outOfStock,
    overstocked,
    totalValue,
    healthScore,
    items: analyzedItems,
  };
}
