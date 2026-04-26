import Image from "next/image";
import Link from "next/link";
import {ShieldCheck, BarChart, UserSearch, AlertTriangle} from "lucide-react"; 

const features = [
  {
    name: 'Company Overview',
    description: 'Get comprehensive profiles including business models, market presence, and more.',
    icon: <ShieldCheck className="w-8 h-8 text-blue-500" />
  },
  {
    name: 'Management Research',
    description: 'Verify backgrounds of key executives to identify potential red flags or past controversies.',
    icon: <UserSearch className="w-8 h-8 text-blue-500" />
  },
  {
    name: 'Financial Analysis',
    description: 'Detect accounting anomalies, unusual revenue patterns, and other financial integrity concerns.',
    icon: <BarChart className="w-8 h-8 text-blue-500" />
  },
  {
    name: 'Scam Detection',
    description: 'Analyze trading patterns to spot volume spikes and signs of market manipulation.',
    icon: <AlertTriangle className="w-8 h-8 text-blue-500" />
  }
];
export default function Home() {
  return (
     <div className="bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200">
      {/* Hero Section */}
      <main className="container mx-auto px-6 pt-32 pb-16 text-center">
        <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-4">
          Invest with Confidence.
        </h1>
        <p className="text-lg md:text-xl text-zinc-600 dark:text-zinc-400 max-w-3xl mx-auto mb-8">
          Signal Sync provides AI-powered background verification on companies, helping retail investors make smarter, more informed decisions.
        </p>
        <Link href="/signup" className="bg-blue-600 text-white px-8 py-3 rounded-md text-lg font-semibold hover:bg-blue-500 transition-transform transform hover:scale-105">
          Get Started for Free
        </Link>
      </main>

      {/* Features Section */}
      <section id="features" className="py-20 bg-zinc-50 dark:bg-zinc-800">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold">Comprehensive BGV for Investors</h2>
            <p className="text-md text-zinc-600 dark:text-zinc-400 mt-2">We analyze every angle to give you a clear picture.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => (
              <div key={feature.name} className="bg-white dark:bg-zinc-700 p-6 rounded-lg shadow-md text-center">
                <div className="flex justify-center mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.name}</h3>
                <p className="text-zinc-600 dark:text-zinc-300">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
