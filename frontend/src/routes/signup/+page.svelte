<script>
  import Button from "$lib/components/ui/button/button.svelte"
  import Input from "$lib/components/ui/input/input.svelte"
  import Label from "$lib/components/ui/label/label.svelte"
  import "../../app.css"
</script>

<div class="flex justify-center items-center grow">
  <div class="flex flex-col max-w-xl w-full p-4 border rounded-2xl">
    <div class="flex justify-end">
      <Button href="/login" variant="ghost">Log in</Button>
    </div>
    <div class="flex justify-center items-center grow py-64">
      <div class="flex flex-col w-full max-w-sm gap-6">
        <h1 class="text-2xl font-semibold text-center">Create an account</h1>
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-2">
            <Label for="username">Username</Label>
            <Input id="username" />
          </div>
          <Button>Continue</Button>
        </div>
      </div>
    </div>
  </div>
</div>
