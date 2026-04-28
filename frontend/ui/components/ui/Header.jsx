"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import SearchBar from "./SearchBar";
import { createClient } from "../../lib/supabase/client";

export default function Header() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const supabase = createClient();

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setReady(true);
    });

    // Keep in sync with auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/?msg=logout");
  };

  // Avoid flash of wrong state on first render
  
    

  return (
    <header className="absolute top-0 left-0 right-0 z-10 bg-transparent">
      <nav className="container mx-auto px-6 py-4 flex items-center justify-between">

  {/* LEFT: Logo */}
  <div className="text-2xl font-bold text-zinc-800 dark:text-white">
    <Link href="/">Signal Sync</Link>
  </div>

  {/* CENTER: SearchBar */}
  <div className="flex-1 mx-6 max-w-xl">
    <SearchBar />
  </div>

  {/* RIGHT: Auth */}
  <div className="flex items-center space-x-4">
    {user ? (
      <>
        <button
          type="button"
          onClick={() => router.push("/profile")}
          className="hidden text-sm text-zinc-600 transition hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200 sm:block"
        >
          {user.user_metadata?.full_name || user.email}
        </button>
        <button
          onClick={handleLogout}
          className="bg-zinc-800 text-white px-4 py-2 rounded-md hover:bg-zinc-700 transition-colors text-sm"
        >
          Logout
        </button>
      </>
    ) : (
      <>
        <Link
          href="/login"
          className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-white transition-colors"
        >
          Login
        </Link>
        <Link
          href="/signup"
          className="bg-zinc-800 text-white px-4 py-2 rounded-md hover:bg-zinc-700 transition-colors"
        >
          Sign Up
        </Link>
      </>
    )}
  </div>

      </nav>
    </header>
  );
}
