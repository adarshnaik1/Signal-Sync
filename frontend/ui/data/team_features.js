import { ShieldCheck, BarChart, UserSearch, AlertTriangle } from "lucide-react";
const features = [
  {
    name: "Fully Agentic Fundamental Analysis",
    description: "Let our AI agents perform deep fundamental analysis of stocks for you.",
    icon: <BarChart className="w-8 h-8 text-blue-500" />,
  },
  {
    name: "Fully Agentic Technical Analysis",
    description: "Automated technical analysis to identify trends and patterns.",
    icon: <AlertTriangle className="w-8 h-8 text-blue-500" />,
  },
  {
    name: "Fully Agentic  Portfolio Recommendations",
    description: "Receive portfolio recommendations based on your risk profile and goals.",
    icon: <UserSearch className="w-8 h-8 text-blue-500" />,
  },
  {
    name: "ML Powered Personalised Portfolio Recommendation",
    description: "Get a personalized portfolio created by our machine learning models.",
    icon: <ShieldCheck className="w-8 h-8 text-blue-500" />,
  },
];
export default features