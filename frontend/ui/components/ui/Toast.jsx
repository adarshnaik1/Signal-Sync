"use client";

import { useEffect, useState } from "react";

export default function Toast({ message, onDone }) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      onDone?.();
    }, 3500);
    return () => clearTimeout(timer);
  }, [onDone]);

  if (!visible) return null;

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-zinc-800 dark:bg-zinc-100 text-white dark:text-zinc-900 text-sm font-medium px-6 py-3 rounded-md shadow-lg transition-opacity">
      {message}
    </div>
  );
}
