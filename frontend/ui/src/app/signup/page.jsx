"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Input from "../../../components/ui/Input";
import Button from "../../../components/ui/Button";
import FormContainer from "../../../components/ui/FormContainer";
import { createClient } from "../../../lib/supabase/client";

export default function SignupPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (form.password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    if (form.password !== form.confirm) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    const supabase = createClient();

    const { error } = await supabase.auth.signUp({
      email: form.email,
      password: form.password,
      options: {
        data: { full_name: form.name },
      },
    });

    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    // Sign out immediately — user should log in manually after signup
    const supabase2 = createClient();
    await supabase2.auth.signOut();

    router.push("/?msg=signup");
  };

  return (
    <FormContainer title="Create an account" subtitle="Start investing with confidence today">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <Input
          label="Full Name"
          id="name"
          type="text"
          placeholder="John Doe"
          value={form.name}
          onChange={handleChange("name")}
          required
        />
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
          placeholder="Min. 6 characters"
          value={form.password}
          onChange={handleChange("password")}
          required
        />
        <Input
          label="Confirm Password"
          id="confirm"
          type="password"
          placeholder="••••••••"
          value={form.confirm}
          onChange={handleChange("confirm")}
          required
        />

        {error && (
          <p className="text-sm text-red-500 text-center">{error}</p>
        )}

        <Button type="submit" variant="primary" disabled={loading}>
          {loading ? "Creating account..." : "Create Account"}
        </Button>
      </form>

      <p className="text-center text-sm text-zinc-600 dark:text-zinc-400 mt-6">
        Already have an account?{" "}
        <Link href="/login" className="text-blue-500 hover:text-blue-400 font-medium transition-colors">
          Login
        </Link>
      </p>
    </FormContainer>
  );
}
