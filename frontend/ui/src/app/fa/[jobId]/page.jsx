import FAAnalysisClient from "../../../../components/fa/FAAnalysisClient";

export default async function FAAnalysisPage({ params }) {
  const { jobId } = (await params) ?? {};

  return <FAAnalysisClient jobId={String(jobId || "")} />;
}