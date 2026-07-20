import NewsAnalysisClient from "../../../../components/news/NewsAnalysisClient";

export default async function NewsAnalysisPage({ params }) {
  const { jobId } = (await params) ?? {};

  return <NewsAnalysisClient jobId={String(jobId || "")} />;
}
