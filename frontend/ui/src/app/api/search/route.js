import { createClient } from "@lib/supabase/client"

export async function GET(req){
    const { searchParams } = new URL(req.url)
    const query = searchParams.get("query")

    if(!query){
        return Response.json([])
    }
    const client = createClient()

    const {data, error}= await client
    .from("companies")
    .select("ticker, company_name")
    .ilike("ticker",`%${query}%`)
    .limit(10)

    if(error){
        console.error("Error fetching search results:", error)
        return Response.json([], {status: 500})
    }
    
    return Response.json(data)


}