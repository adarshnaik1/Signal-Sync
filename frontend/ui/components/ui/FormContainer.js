export default function FormContainer({ title, subtitle, children }) {
  return (
    <div className="min-h-screen bg-white dark:bg-zinc-900 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-zinc-50 dark:bg-zinc-800 rounded-lg shadow-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-zinc-800 dark:text-zinc-100">{title}</h1>
          {subtitle && (
            <p className="text-zinc-600 dark:text-zinc-400 mt-2 text-sm">{subtitle}</p>
          )}
        </div>
        {children}
      </div>
    </div>
  );
}
