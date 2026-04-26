"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Input from "../../../components/ui/Input";
import Button from "../../../components/ui/Button";
import FormContainer from "../../../components/ui/FormContainer";
import { createClient } from "../../../lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const supabase = createClient();
    const { error } = await supabase.auth.signInWithPassword({
      email: form.email,
      password: form.password,
    });

    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    router.push("/?msg=login");
  };

  return (
    <FormContainer title="Welcome back" subtitle="Sign in to your Signal Sync account">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <Input
          label="Email"
          id="email"
          type="email"
          placeholder="you@example.com"
          value={form.email}
          onChange={handleChange("email")}
          required
        />
        <Input
          label="Password"
          id="password"
          type="password"
          placeholder="••••••••"
          value={form.password}
          onChange={handleChange("password")}
          required
        />

        {error && (
          <p className="text-sm text-red-500 text-center">{error}</p>
        )}

        <Button type="submit" variant="primary" disabled={loading}>
          {loading ? "Signing in..." : "Login"}
        </Button>
      </form>

      <p className="text-center text-sm text-zinc-600 dark:text-zinc-400 mt-6">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-blue-500 hover:text-blue-400 font-medium transition-colors">
          Sign up
        </Link>
      </p>
    </FormContainer>
  );
}
