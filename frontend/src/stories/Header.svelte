<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import '../app.css';
	import ProfileMenu from './ProfileMenu.svelte';

	interface Props {
		user?: User;
		onLogin?: () => void;
		onLogout?: () => void;
		onCreateAccount?: () => void;
	}

	const { user, onLogin, onLogout, onCreateAccount: onSignUp }: Props = $props();
</script>

<header class="h-16 border-b flex items-center px-4 shrink-0 justify-between">
	s
	<div class="flex items-center gap-2">
		{#if user}
			<ProfileMenu {user} {onLogout} />
		{:else}
			<Button onclick={onLogin} variant="secondary">Log in</Button>
			<Button onclick={onSignUp}>Sign up</Button>
		{/if}
	</div>
</header>
