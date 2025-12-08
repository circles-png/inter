<script lang="ts">
  import { Skeleton } from "$lib/components/ui/skeleton"
</script>

<main class="p-2 flex flex-col gap-2 overflow-y-auto grow pr-0">
  {#each { length: 6 }}
    <div class="flex flex-col gap-2">
      <Skeleton class="w-50 h-6" />
      <div class="flex gap-2 overflow-x-auto pb-1">
        {#each { length: 7 }}
          <div class="flex flex-col gap-2 grow">
            <Skeleton class="aspect-video w-96" />
            <div class="flex gap-2">
              <Skeleton class="size-10 rounded-full" />
              <div class="flex flex-col gap-1 grow">
                <Skeleton class="w-20 h-4" />
                <Skeleton class="w-30 h-3" />
                <Skeleton class="w-15 h-3" />
              </div>
              <Skeleton class="md:w-10 md:h-3 rounded-full" />
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/each}
</main>
