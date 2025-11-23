<script lang="ts">
	import { Avatar } from '$lib/components/ui/avatar';
	import '../app.css';

	interface Props {
		user: User
		onLogout?: () => void;
	}

	const { user, onLogout }: Props = $props();
</script>

<button onclick={() => {

}}>
	<Avatar image={user.avatar} size="small" alt="Profile" />
</button>
