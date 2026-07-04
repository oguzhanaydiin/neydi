<script setup lang="ts">
import type { LoginPayload } from '~/composables/useAuth'

definePageMeta({ layout: 'auth' })

useSeoMeta({ title: 'Sign in - neydi' })

const { login } = useAuth()
const { migrateLocalDecks, loadDecks } = useDecks()
const toast = useToast()
const router = useRouter()

const form = reactive<LoginPayload>({
  email: '',
  password: ''
})

const loading = ref(false)
const serverError = ref('')

const validate = (state: LoginPayload) => {
  const errors: { path: string, message: string }[] = []
  if (!state.email) errors.push({ path: 'email', message: 'Email is required' })
  if (!state.password) errors.push({ path: 'password', message: 'Password is required' })
  return errors
}

const onSubmit = async () => {
  serverError.value = ''
  loading.value = true
  try {
    await login(form)
    await migrateLocalDecks()
    await loadDecks()
    toast.add({ title: 'Welcome back!', color: 'success' })
    await router.push('/')
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string }, message?: string }
    serverError.value = e?.data?.detail ?? e?.message ?? 'Invalid credentials. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-16">
    <div class="w-full max-w-sm">
      <div class="mb-8 text-center">
        <NuxtLink
          to="/"
          class="text-2xl font-bold tracking-tight text-primary"
        >
          neydi
        </NuxtLink>
        <h1 class="mt-4 text-xl font-semibold">
          Welcome back
        </h1>
        <p class="text-sm text-muted mt-1">
          Sign in to continue learning
        </p>
      </div>

      <UCard>
        <UForm
          :validate="validate"
          :state="form"
          class="space-y-4"
          @submit="onSubmit"
        >
          <UAlert
            v-if="serverError"
            color="error"
            variant="soft"
            :description="serverError"
            icon="i-lucide-circle-alert"
          />

          <UFormField
            label="Email"
            name="email"
          >
            <UInput
              v-model="form.email"
              type="email"
              placeholder="you@example.com"
              autocomplete="email"
              class="w-full"
            />
          </UFormField>

          <UFormField
            label="Password"
            name="password"
          >
            <UInput
              v-model="form.password"
              type="password"
              placeholder="Your password"
              autocomplete="current-password"
              class="w-full"
            />
          </UFormField>

          <UButton
            type="submit"
            block
            :loading="loading"
            class="mt-2"
          >
            Sign in
          </UButton>
        </UForm>
      </UCard>

      <p class="mt-6 text-center text-sm text-muted">
        Don't have an account?
        <NuxtLink
          to="/register"
          class="text-primary font-medium hover:underline"
        >
          Create one
        </NuxtLink>
      </p>
    </div>
  </div>
</template>
