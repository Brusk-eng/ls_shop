// An Item's name is free text: an unencoded `/` splits it into extra route segments and a `?`
// starts a query string, so either lands on "nothing at this address".
export function productRoute(productName, variantName) {
  const path = `/products/${encodeURIComponent(productName)}`
  return variantName ? `${path}/variants/${encodeURIComponent(variantName)}` : path
}
