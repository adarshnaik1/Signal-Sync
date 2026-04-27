"use client"

import {useEffect, useState } from "react";
import{useRouter} from "next/navigation"


export default  function SearchBar(){
    const [query, setQuery] = useState("");
    const [show, setShow] = useState(false);
    const[results, setResults] = useState([]);
    
    const router = useRouter();

    useEffect(()=>{
        const delay = setTimeout(()=>{
            if(query.length > 2){
                fetchResults(query)
                setShow(true)
            }
            else{
                setResults([])
                setShow(false)
            }

        },300)

        return ()=>{ clearTimeout(delay)}
    },[query])


    async function fetchResults(query){
        const res = await fetch(`api/search?query=${query}`)
        const data = await res.json();
        setResults(data)
     }
    
     function handleSelect(symbol){
        setQuery("")
        setShow(false)
        router.push(`stocks/${symbol}`)
     }
    return (
        <div className=" relative w-96">
            <input className="w-full rounded-lg p-2 border-gray-600 border-2" 
            type="text"
            placeholder="Seach Stocks ..."
            value={query}
            onChange={(e)=> setQuery(e.target.value)}
            >

            </input>

            {/*The Search Results */}
            {show && results.length >0 && (
                <div className="absolute bg-gray-700 text-white mt-2">
                    {results.map((result)=>(
                        
                        <div
                         key={result.ticker}
                        className=" p-2 hover:bg-gray-500 lg:w-90 cursor-pointer border-b border-gray-600"
                        onClick={()=> handleSelect(result.ticker)}>
                            <div className="font-medium">{result.company_name}</div>
                            <div className="text-sm text-gray-500">{result.ticker}</div>

                        </div>
                    ))}
                </div>
            )}

        </div>
    )
}