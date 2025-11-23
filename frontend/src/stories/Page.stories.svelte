<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import Page from './Page.svelte';

	const { Story } = defineMeta({
		title: 'Components/Page',
		component: Page,
		parameters: {
			layout: 'fullscreen'
		}
	});
</script>

<Story name="Logged In" />

<Story name="Logged Out" />
