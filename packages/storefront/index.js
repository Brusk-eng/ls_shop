const API_ROOT = '/api/method/commera.api.storefront';

export async function get_storefront_data(
	method,
	params = {},
	{ base_url = '' } = {},
) {
	const query = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined && value !== null) {
			query.set(key, typeof value === 'object' ? JSON.stringify(value) : value);
		}
	}
	const response = await fetch(`${base_url}${API_ROOT}.${method}?${query}`, {
		credentials: 'include',
		headers: { Accept: 'application/json' },
	});
	const body = await response.json().catch(() => ({}));
	if (!response.ok) {
		throw new Error(
			body.exception || body._error_message || response.statusText,
		);
	}
	return body.message;
}
