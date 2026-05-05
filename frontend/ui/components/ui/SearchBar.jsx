"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const [show, setShow] = useState(false);
  const [results, setResults] = useState([]);
  const router = useRouter();

  async function fetchResults(searchTerm) {
    const res = await fetch(`/api/search?query=${searchTerm}`);
    const data = await res.json();
    setResults(data);
  }

  useEffect(() => {
    const delay = setTimeout(() => {
      if (query.length > 2) {
        fetchResults(query);
        setShow(true);
      } else {
        setResults([]);
        setShow(false);
      }
    }, 300);

    return () => {
      clearTimeout(delay);
    };
  }, [query]);

  function handleSelect(symbol) {
    setQuery("");
    setShow(false);
    router.push(`/stocks/${symbol}`);
  }

  return (
    <div className="relative w-96">
      <input
        className="w-full rounded-lg border-2 border-gray-600 p-2"
        type="text"
        placeholder="Search Stocks ..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {show && results.length > 0 ? (
        <div className="absolute mt-2 bg-gray-700 text-white">
          {results.map((result) => (
            <div
              key={result.ticker}
              className="cursor-pointer border-b border-gray-600 p-2 hover:bg-gray-500 lg:w-90"
              onClick={() => handleSelect(result.ticker)}
            >
              <div className="font-medium">{result.company_name}</div>
              <div className="text-sm text-gray-500">{result.ticker}</div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
