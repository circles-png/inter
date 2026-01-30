<script lang="ts">
  import { invalidateAll } from "$app/navigation"
  import { resolve } from "$app/paths"
  import { Avatar, AvatarFallback, AvatarImage } from "$lib/components/ui/avatar"
  import BellRing from "@lucide/svelte/icons/bell-ring"
  import BellOff from "@lucide/svelte/icons/bell-off"

  import { Button } from "$lib/components/ui/button"
  import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectLabel,
    SelectTrigger,
  } from "$lib/components/ui/select/"
  import { colours, server } from "$lib/utils.svelte"
  import { PUBLIC_VAPID_KEY } from "$env/static/public"
  import { Spinner } from "$lib/components/ui/spinner"

  let { data } = $props()
  const user = $derived(data.user)
  const profile = $derived(data.profile)
  const following = $derived(data.following)
  const stream = $derived(data.stream)
  const username = $derived(profile.username)
  const avatar = $derived(server.user.avatar(username))
  let updatingNotify = $state(false)
</script>

<div class="flex flex-col p-2 gap-4 grow">
  <div
    class="aspect-3/1 rounded-md border"
    style:background-color={colours[profile.colour]}
    style:background-repeat="no-repeat"
  ></div>
  {#key avatar}
    <div class="flex gap-4 border rounded-md p-4 items-center flex-wrap">
      <Avatar class="size-16">
        <AvatarImage src={avatar} alt={username} />
        <AvatarFallback class="bg-muted" />
      </Avatar>
      <div class="flex flex-col grow">
        <div class="font-bold">{profile.displayName || `@${username}`}</div>
        {#if profile.displayName}
          <div class="text-sm text-muted-foreground">@{username}</div>
        {/if}
        <div class="text-sm flex gap-4">
          <div>{profile.followers} {profile.followers == 1 ? "follower" : "followers"}</div>
          <div>{profile.following} following</div>
        </div>
      </div>
      <div class="flex gap-4 flex-wrap">
        <Button
          href={resolve("/(main)/@[username=user]/watch", { username })}
          data-sveltekit-reload
        >
          {#if stream.start}
            Watch
          {:else}
            Chat
          {/if}
        </Button>
        {#if user && username != user.username}
          {#if following.some((following) => following.username == username)}
            <Button
              onclick={async () => {
                await server.user.unfollow(username)
                await invalidateAll()
              }}
              variant="outline"
            >
              Unfollow
            </Button>
            <Select
              type="single"
              name="notifications"
              value={data.notify}
              onValueChange={async (value) => {
                updatingNotify = true
                if (value == "all") {
                  const result = await Notification.requestPermission()
                  if (result != "granted") return
                  const registration = await navigator.serviceWorker.ready
                  const subscription =
                    (await registration.pushManager.getSubscription())
                    || (await registration.pushManager.subscribe({
                      userVisibleOnly: true,
                      applicationServerKey: PUBLIC_VAPID_KEY,
                    }))
                  const [p256dh, auth] = [
                    subscription.getKey("p256dh"),
                    subscription.getKey("auth"),
                  ]
                  if (!p256dh || !auth) return
                  await server.user.setNotify(username, {
                    endpoint: subscription.endpoint,
                    keys: { p256dh, auth },
                  })
                } else {
                  await server.user.setNotify(username, null)
                }
                await invalidateAll()
                updatingNotify = false
              }}
              disabled={updatingNotify}
            >
              <SelectTrigger>
                {#if updatingNotify}
                  <Spinner />
                {:else if data.notify == "all"}
                  <BellRing />
                {:else}
                  <BellOff />
                {/if}
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectLabel>Notification settings</SelectLabel>
                  <SelectItem value="all" label="All" class="flex-wrap">
                    <BellRing />
                    All
                    <span class="text-sm text-muted-foreground">
                      Notify me whenever {profile.displayName || `@${username}`} goes live.
                    </span>
                  </SelectItem>
                  <SelectItem value="none" label="None" class="flex-wrap">
                    <BellOff />
                    None
                    <span class="text-sm text-muted-foreground">
                      Disable all notifications for {profile.displayName || `@${username}`}.
                    </span>
                  </SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          {:else}
            <Button
              onclick={async () => {
                await server.user.follow(username)
                await invalidateAll()
              }}
            >
              Follow
            </Button>
          {/if}
        {/if}
      </div>
    </div>
  {/key}
  {#if stream.start}
    <div class="flex flex-col gap-4">
      <div class="font-bold text-lg">Currently Streaming</div>
      <a
        class="flex flex-col gap-2"
        href={resolve("/(main)/@[username=user]/watch", { username })}
        data-sveltekit-reload
      >
        <img src={server.user.streamPreview(username)} alt={stream.title} class="w-80 rounded-md" />
        <div class="flex flex-col">
          <div class="font-bold">{stream.title}</div>
          <div class="text-sm text-muted-foreground">
            {stream.game} · {stream.viewers} viewers
          </div>
        </div>
      </a>
    </div>
  {/if}
</div>
