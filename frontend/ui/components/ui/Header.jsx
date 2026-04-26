import { headers } from "next/headers";
import Link from "next/link";

export default function Header() {
    return (
        <header className="absolute top-0 left-0 right-0 z-10 bg-transparent">
            <nav className="container mx-auto px-6 py-4 flex justify-between items-center">
                <div className="text-2xl font-bold text-zinc-800 dark:text-white">
                    <Link href="/">Signal Sync</Link>
                </div>
                <div className="flex items-center space-x-4">
                    <Link href="/login" className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-white transition-colors">
                        Login
                    </Link>
                    <Link href="/signup" className="bg-zinc-800 text-white px-4 py-2 rounded-md hover:bg-zinc-700 transition-colors">
                        Sign Up
                    </Link>
                </div>
            </nav>
        </header>
    )
}