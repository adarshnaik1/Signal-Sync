import TAAnalysisClient from "../../../../components/ta/TAAnalysisClient";

export default async function TAAnalysisPage({ params }) {
  const { jobId } = (await params) ?? {};

  return <TAAnalysisClient jobId={String(jobId || "")} />;
}