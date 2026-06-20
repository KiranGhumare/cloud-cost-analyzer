import { useState } from "react"

const API_URL = "http://localhost:8000"

function App() {
  const [loading, setLoading] = useState(false)
  const [findings, setFindings] = useState([])
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState(null)

  async function runAnalysis() {
    setLoading(true)
    setError(null)
    setFindings([])
    setSummary(null)

    try {
      const response = await fetch(`${API_URL}/analyse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ region: "us-east-1", use_mock_data: true })
      })
      const data = await response.json()
      setFindings(data.findings)
      setSummary(data.telemetry_summary)
    } catch (err) {
      setError("Failed to connect to backend. Make sure it's running.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <h1 className="text-3xl font-bold text-green-400 mb-2">☁️ Cloud Cost Analyser</h1>
      <p className="text-gray-400 mb-8">Agentic AI that finds wasted AWS spend</p>
      
      <button
  onClick={runAnalysis}
  disabled={loading}
  className="bg-green-500 hover:bg-green-400 disabled:bg-gray-600 disabled:cursor-not-allowed text-black font-semibold px-6 py-3 rounded-lg transition-colors mb-8"
>
  {loading ? "Analysing..." : "Run Analysis"}
</button>
      {summary && (
  <div className="bg-gray-800 rounded-lg p-4 mb-6 flex gap-8">
    <div>
      <p className="text-gray-400 text-sm">EC2 Instances Scanned</p>
      <p className="text-2xl font-bold text-white">{summary.ec2_instances_scanned}</p>
    </div>
    <div>
      <p className="text-gray-400 text-sm">Storage Resources Scanned</p>
      <p className="text-2xl font-bold text-white">{summary.storage_resources_scanned}</p>
    </div>
  </div>
)}
      {error && (
  <div className="bg-red-900 border border-red-500 text-red-200 px-4 py-3 rounded-lg mb-6">
    {error}
  </div>
)}
      {findings.length > 0 && (
  <div className="space-y-4">
    <h2 className="text-xl font-semibold text-white mb-4">
      Findings ({findings.filter(f => !f.total_potential_saving).length})
    </h2>
    {findings.map((finding, index) => (
      finding.total_potential_saving ? (
        <div key={index} className="bg-green-900 border border-green-500 rounded-lg p-4">
          <p className="text-green-300 font-semibold text-lg">
            💰 Total Potential Saving: ${finding.total_potential_saving}/month
          </p>
        </div>
      ) : (
        <div key={index} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="flex justify-between items-start mb-2">
            <span className="text-yellow-400 font-semibold">{finding.finding_type}</span>
            <span className="bg-green-800 text-green-300 text-sm px-2 py-1 rounded">
              ${finding.estimated_monthly_saving}/mo saved
            </span>
          </div>
          <p className="text-gray-300 text-sm mb-1">
            <span className="text-gray-500">Resource: </span>{finding.resource_id}
          </p>
          <p className="text-gray-300 text-sm mb-1">
            <span className="text-gray-500">Evidence: </span>{finding.evidence}
          </p>
          <p className="text-gray-300 text-sm">
            <span className="text-gray-500">Fix: </span>{finding.recommendation}
          </p>
          <div className="mt-2">
            <span className={`text-xs px-2 py-1 rounded ${
              finding.confidence === "High" 
                ? "bg-green-900 text-green-300" 
                : "bg-yellow-900 text-yellow-300"
            }`}>
              {finding.confidence} confidence
            </span>
          </div>
        </div>
      )
    ))}
  </div>
)}
    </div>
  )
}

export default App