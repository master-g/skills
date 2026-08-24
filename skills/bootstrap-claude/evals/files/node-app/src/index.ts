export function totalPrice(items: { price: number }[]): number {
  return items.reduce((sum, it) => sum + it.price, 0);
}
