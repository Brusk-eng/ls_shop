/* Loaded synchronously from the page head: Alpine's core is deferred, so a deferred script here
   would miss alpine:init. */
document.addEventListener('alpine:init', () => {
	Alpine.data('summer_combobox', (settings) => ({
		options: settings.options,
		value: '',
		query: '',
		is_open: false,
		active_index: -1,

		init() {
			/* x-modelable hands over the outer value after init runs, so the first sync waits a tick. */
			this.$nextTick(() => this.refresh_query());
			this.$watch('value', () => this.refresh_query());
		},

		get selected_label() {
			const selected = this.options.find(
				(option) => option.value === this.value,
			);
			return selected ? selected.label : '';
		},

		get matches() {
			const term = this.query.trim().toLowerCase();
			if (!term || term === this.selected_label.toLowerCase())
				return this.options;
			const words = term.split(/\s+/);
			const starting = [];
			const containing = [];
			for (const option of this.options) {
				const label = option.label.toLowerCase();
				if (!words.every((word) => label.includes(word))) continue;
				if (label.startsWith(term)) starting.push(option);
				else containing.push(option);
			}
			return [...starting, ...containing];
		},

		refresh_query() {
			this.query = this.selected_label;
			/* A hidden required input makes the browser drop the submit silently; flagging the
			   visible text box instead gets the native bubble on a focusable control. */
			const is_missing = settings.required && !this.value;
			this.$refs.input.setCustomValidity(
				is_missing ? settings.required_message : '',
			);
		},

		open() {
			if (this.is_open) return;
			this.is_open = true;
			const selected_index = this.matches.findIndex(
				(option) => option.value === this.value,
			);
			this.active_index = Math.max(selected_index, 0);
			this.scroll_to_active();
		},

		close() {
			if (!this.is_open) return;
			this.is_open = false;
			this.active_index = -1;
			this.set_value_from_query();
		},

		show_matches() {
			this.is_open = true;
			this.active_index = this.matches.length ? 0 : -1;
			this.$refs.listbox.scrollTop = 0;
		},

		set_value_from_query() {
			const term = this.query.trim().toLowerCase();
			const exact_match = this.options.find(
				(option) => option.label.toLowerCase() === term,
			);
			if (exact_match) this.value = exact_match.value;
			else if (!term) this.value = '';
			this.refresh_query();
		},

		move_active(step) {
			if (!this.is_open) return this.open();
			const last_index = this.matches.length - 1;
			this.active_index = Math.min(
				Math.max(this.active_index + step, 0),
				last_index,
			);
			this.scroll_to_active();
		},

		select_active(event) {
			if (!this.is_open) return;
			event.preventDefault();
			const option = this.matches[this.active_index];
			if (option) this.select(option);
		},

		select(option) {
			this.value = option.value;
			this.is_open = false;
			this.active_index = -1;
			this.refresh_query();
			this.$refs.input.focus();
		},

		scroll_to_active() {
			this.$nextTick(() => {
				const option = this.$refs.listbox.querySelector('.active');
				if (option) option.scrollIntoView({ block: 'nearest' });
			});
		},
	}));
});
