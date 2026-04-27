export default function Button({ children, type = "button", onClick, variant = "primary", disabled }) {
  const styles = {
    primary: "bg-blue-600 text-white hover:bg-blue-500",
    secondary: "bg-zinc-800 text-white hover:bg-zinc-700",
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`w-full px-8 py-3 rounded-md text-base font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${styles[variant]}`}
    >
      {children}
    </button>
  );
}
