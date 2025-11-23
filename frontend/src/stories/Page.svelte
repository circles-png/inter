<script lang="ts">
	import Header from './Header.svelte';
	import '../app.css';

	let user = $state<User>();
	const { content } = $props();
</script>

<Header
	{user}
	onLogin={() => (user = { id: 1, username: 'User', avatar: 'http://picsum.photos/200' })}
	onLogout={() => (user = undefined)}
	onCreateAccount={() => (user = { id: 1, username: 'User', avatar: 'http://picsum.photos/200' })}
/>

{content}
