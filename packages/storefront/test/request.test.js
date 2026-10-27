import assert from 'node:assert/strict';
import { beforeEach, test } from 'node:test';
import { StorefrontError, get, post } from '../request.js';
import { add_fake_fetch } from './fake-fetch.js';

beforeEach(() => {
	globalThis.commera_storefront_config = { csrf_token: 'csrf-123' };
	globalThis.frappe = undefined;
});

test('get sends arguments in the query string and unwraps message', async () => {
	const calls = add_fake_fetch({
		get_products: { body: { message: { products: [] } } },
	});
	const result = await get('products.get_products', {
		collection: 'shoes',
		brands: ['Nike', 'Puma'],
		query: null,
	});
	assert.deepEqual(result, { products: [] });
	assert.equal(
		calls[0].url,
		'/api/method/commera.api.storefront.products.get_products?collection=shoes&brands=%5B%22Nike%22%2C%22Puma%22%5D',
	);
	assert.equal(calls[0].options.method, 'GET');
	assert.equal(calls[0].options.credentials, 'same-origin');
});

test('get without arguments has no query string', async () => {
	const calls = add_fake_fetch();
	await get('cart.get_cart');
	assert.equal(
		calls[0].url,
		'/api/method/commera.api.storefront.cart.get_cart',
	);
});

test('post sends a JSON body with the CSRF token', async () => {
	const calls = add_fake_fetch();
	await post('cart.add_lines', { lines: [{ item_code: 'SHOE-42', qty: 1 }] });
	assert.equal(calls[0].options.method, 'POST');
	assert.equal(calls[0].options.headers['X-Frappe-CSRF-Token'], 'csrf-123');
	assert.equal(calls[0].options.headers['Content-Type'], 'application/json');
	assert.deepEqual(calls[0].body, {
		lines: [{ item_code: 'SHOE-42', qty: 1 }],
	});
});

test('post falls back to frappe.csrf_token on a page without the config', async () => {
	globalThis.commera_storefront_config = undefined;
	globalThis.frappe = { csrf_token: 'desk-csrf' };
	const calls = add_fake_fetch();
	await post('cart.get_checkout_url');
	assert.equal(calls[0].options.headers['X-Frappe-CSRF-Token'], 'desk-csrf');
});

test('a failed call throws the first server message without HTML', async () => {
	add_fake_fetch({
		add_discount_code: {
			status: 417,
			body: {
				exc_type: 'ValidationError',
				exception: 'frappe.exceptions.ValidationError: Code SAVE10 has expired',
				_server_messages: JSON.stringify([
					JSON.stringify({ message: 'Code <b>SAVE10</b> has expired' }),
				]),
			},
		},
	});
	await assert.rejects(post('cart.add_discount_code', { code: 'SAVE10' }), {
		name: 'StorefrontError',
		message: 'Code SAVE10 has expired',
		status: 417,
		exc_type: 'ValidationError',
	});
});

test('a failed call without server messages throws the exception', async () => {
	add_fake_fetch({
		get_wishlist: {
			status: 403,
			body: {
				exc_type: 'PermissionError',
				exception: 'frappe.exceptions.PermissionError',
			},
		},
	});
	const error = await get('wishlist.get_wishlist').catch((error) => error);
	assert.ok(error instanceof StorefrontError);
	assert.equal(error.message, 'frappe.exceptions.PermissionError');
	assert.equal(error.exc_type, 'PermissionError');
});

test('a failed call with no JSON body throws the status text', async () => {
	globalThis.fetch = async () => ({
		ok: false,
		status: 502,
		statusText: 'Bad Gateway',
		json: async () => {
			throw new SyntaxError('Unexpected token <');
		},
	});
	await assert.rejects(get('cart.get_cart'), {
		message: 'Bad Gateway',
		status: 502,
	});
});
