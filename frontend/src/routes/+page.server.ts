import { getStreamEndpoint } from "$lib/utils.svelte";
import { redirect } from "@sveltejs/kit";

export async function load() {
  redirect(302, await (await fetch(getStreamEndpoint("host.docker.internal", "http", "random", "5001"))).text());
}
