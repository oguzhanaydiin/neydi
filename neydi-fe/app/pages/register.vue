<script setup lang="ts">
import type { RegisterPayload } from '~/composables/useAuth'

definePageMeta({ layout: 'auth' })

useSeoMeta({ title: 'Register - neydi' })

const { register } = useAuth()
const toast = useToast()
const router = useRouter()

const form = reactive<RegisterPayload>({
  email: '',
  username: '',
  password: ''
})

const confirmPassword = ref('')
const loading = ref(false)
const serverError = ref('')

const validate = (state: RegisterPayload) => {
  const errors: { path: string, message: string }[] = []

  if (!state.email) {
    errors.push({ path: 'email', message: 'Email is required' })
  }
  if (!state.username) {
    errors.push({ path: 'username', message: 'Username is required' })
  } else if (!/^[a-z0-9]+$/i.test(state.username)) {
    errors.push({ path: 'username', message: 'Username must be alphanumeric' })
  } else if (state.username.length < 3 || state.username.length > 50) {
    errors.push({ path: 'username', message: 'Username must be 3–50 characters' })
  }
  if (!state.password) {
    errors.push({ path: 'password', message: 'Password is required' })
  } else if (state.password.length < 8) {
    errors.push({ path: 'password', message: 'Password must be at least 8 characters' })
  }
  if (confirmPassword.value && state.password !== confirmPassword.value) {
    errors.push({ path: 'confirmPassword', message: 'Passwords do not match' })
  }

  return errors
}

const onSubmit = async () => {
  serverError.value = ''
  loading.value = true
  try {
    await register(form)
    toast.add({
      title: 'Account created!',
      description: 'You can now log in with your credentials.',
      color: 'success'
    })
    await router.push('/login')
  } catch (err: unknown) {
    const e = err as { data?: { detail?: string } }
    serverError.value = e?.data?.detail ?? 'Something went wrong. Please try again.'
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
          Create an account
        </h1>
        <p class="text-sm text-muted mt-1">
          Start learning and remembering more
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
            label="Username"
            name="username"
            hint="Letters and numbers only"
          >
            <UInput
              v-model="form.username"
              placeholder="cooluser42"
              autocomplete="username"
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
              placeholder="Min. 8 characters"
              autocomplete="new-password"
              class="w-full"
            />
          </UFormField>

          <UFormField
            label="Confirm password"
            name="confirmPassword"
          >
            <UInput
              v-model="confirmPassword"
              type="password"
              placeholder="Repeat your password"
              autocomplete="new-password"
              class="w-full"
            />
          </UFormField>

          <UButton
            type="submit"
            block
            :loading="loading"
            class="mt-2"
          >
            Create account
          </UButton>
        </UForm>
      </UCard>

      <p class="mt-6 text-center text-sm text-muted">
        Already have an account?
        <NuxtLink
          to="/login"
          class="text-primary font-medium hover:underline"
        >
          Sign in
        </NuxtLink>
      </p>
    </div>
  </div>
</template>
