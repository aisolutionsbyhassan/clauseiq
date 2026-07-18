import React, { useState, useEffect } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { contractsApi } from '@/api/contractsApi';
import { analysisApi } from '@/api/analysisApi';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, MessageSquare, AlertTriangle, Play, CheckCircle2, Download } from 'lucide-react';

export default function ContractDetail() {
  const { contractId } = useParams();
  const location = useLocation();
  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const [activeTab, setActiveTab] = useState(location.state?.highlightChunk !== undefined ? "clauses" : "summary");
  const [highlightedClauseId, setHighlightedClauseId] = useState(null);
  
  const [clausesData, setClausesData] = useState(null);
  const [risksData, setRisksData] = useState(null);
  const [summaryData, setSummaryData] = useState(null);
  
  const [actionLoading, setActionLoading] = useState(false);

  const loadContract = async () => {
    try {
      const data = await contractsApi.getContract(contractId);
      setContract(data);
    } catch (err) {
      console.error("Failed to load contract", err);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalysisData = async () => {
    try {
      const [c, r, s] = await Promise.allSettled([
        analysisApi.getClauses(contractId),
        analysisApi.getRisks(contractId),
        analysisApi.getSummary(contractId)
      ]);
      
      if (c.status === 'fulfilled' && c.value.clauses.length > 0) {
        setClausesData(c.value.clauses);
        
        // Handle clause highlighting from search
        const targetChunk = location.state?.highlightChunk;
        if (targetChunk !== undefined) {
          const matchingClause = c.value.clauses.find(clause => 
            clause.is_present && clause.source_chunk_ids && clause.source_chunk_ids.includes(targetChunk)
          );
          if (matchingClause) {
            setHighlightedClauseId(matchingClause.id);
            // Give DOM time to render the clauses tab before scrolling
            setTimeout(() => {
              const el = document.getElementById(`clause-${matchingClause.id}`);
              if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
              }
            }, 300);
          }
        }
      }
      if (r.status === 'fulfilled' && r.value.risks.length > 0) setRisksData(r.value.risks);
      if (s.status === 'fulfilled') setSummaryData(s.value);
    } catch (err) {
      console.error("Failed to load analysis data", err);
    }
  };

  useEffect(() => {
    loadContract();
    loadAnalysisData();
  }, [contractId]);

  const handleExtractClauses = async () => {
    setActionLoading(true);
    try {
      const res = await analysisApi.extractClauses(contractId);
      setClausesData(res.clauses);
    } catch (err) {
      alert("Failed to extract clauses. Ensure document processing is complete.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleDetectRisks = async () => {
    setActionLoading(true);
    try {
      const res = await analysisApi.detectRisks(contractId);
      setRisksData(res.risks);
      loadContract(); // Refresh risk level badge
    } catch (err) {
      alert("Failed to detect risks. Ensure clauses are extracted first.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleGenerateSummary = async () => {
    setActionLoading(true);
    try {
      const res = await analysisApi.generateSummary(contractId);
      setSummaryData(res);
    } catch (err) {
      alert("Failed to generate summary. Ensure clauses and risks are available.");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-full">Loading...</div>;
  if (!contract) return <div>Contract not found.</div>;

  return (
    <div className="flex flex-col gap-8">
      <div>
        <Button variant="ghost" size="sm" className="mb-4 -ml-4" asChild>
          <Link to={`/projects/${contract.project_id}`}><ArrowLeft className="mr-2 h-4 w-4" /> Back to Project</Link>
        </Button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{contract.filename}</h1>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant={contract.processing_status === 'completed' ? 'default' : 'secondary'}>
                Status: {contract.processing_status}
              </Badge>
              <Badge variant={contract.overall_risk_level === 'high' ? 'destructive' : 'outline'}>
                Risk: {contract.overall_risk_level}
              </Badge>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => contractsApi.downloadContract(contract.id, contract.filename)}>
              <Download className="mr-2 h-4 w-4" /> Download Original
            </Button>
            <Button asChild>
              <Link to={`/contracts/${contract.id}/chat`}><MessageSquare className="mr-2 h-4 w-4" /> Chat with Contract</Link>
            </Button>
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="summary">Executive Summary</TabsTrigger>
          <TabsTrigger value="clauses">Extracted Clauses</TabsTrigger>
          <TabsTrigger value="risks">Detected Risks</TabsTrigger>
        </TabsList>

        {/* SUMMARY TAB */}
        <TabsContent value="summary" className="space-y-4">
          {!summaryData ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <p className="text-muted-foreground mb-4">No summary generated yet.</p>
                <Button onClick={handleGenerateSummary} disabled={actionLoading || !clausesData || !risksData}>
                  <Play className="mr-2 h-4 w-4" /> Generate Summary
                </Button>
                {(!clausesData || !risksData) && (
                  <p className="text-xs text-muted-foreground mt-2">Requires Clauses and Risks to be extracted first.</p>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader><CardTitle>Key Obligations</CardTitle></CardHeader>
                <CardContent>
                  <ul className="list-disc pl-5 space-y-1 text-sm">
                    {summaryData.key_obligations?.map((item, i) => (
                      <li key={i}>
                        <span className="font-semibold">{item.party || 'Unknown'}:</span> {item.obligation}
                        {item.deadline && <span className="text-muted-foreground ml-1">(Due: {item.deadline})</span>}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Financial Terms</CardTitle></CardHeader>
                <CardContent>
                  <ul className="list-disc pl-5 space-y-1 text-sm">
                    {summaryData.financial_terms?.map((item, i) => (
                      <li key={i}>
                        <span className="font-semibold">{item.term || 'Term'}:</span> {item.details}
                        {item.impact && <span className="text-muted-foreground ml-1">[{item.impact}]</span>}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Important Dates</CardTitle></CardHeader>
                <CardContent>
                  <ul className="list-disc pl-5 space-y-1 text-sm">
                    {summaryData.important_dates?.map((item, i) => (
                      <li key={i}>
                        <span className="font-semibold">{item.label || 'Date'}:</span> {item.date}
                        {item.significance && <span className="text-muted-foreground ml-1">- {item.significance}</span>}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Major Risks</CardTitle></CardHeader>
                <CardContent>
                  <ul className="list-disc pl-5 space-y-1 text-sm text-destructive">
                    {summaryData.major_risks?.map((item, i) => (
                      <li key={i}>
                        <span className="font-semibold">{item.risk || 'Risk'}:</span> {item.summary}
                        {item.action && <div className="text-muted-foreground text-xs mt-0.5">Action: {item.action}</div>}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* CLAUSES TAB */}
        <TabsContent value="clauses" className="space-y-4">
          {!clausesData ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <p className="text-muted-foreground mb-4">No clauses extracted yet.</p>
                <Button onClick={handleExtractClauses} disabled={actionLoading}>
                  <Play className="mr-2 h-4 w-4" /> Run Clause Extraction
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {clausesData.map(clause => (
                <Card 
                  key={clause.id} 
                  id={`clause-${clause.id}`}
                  className={`${!clause.is_present ? 'opacity-60 bg-muted/20' : ''} ${highlightedClauseId === clause.id ? 'ring-2 ring-primary ring-offset-2 transition-all duration-500' : ''}`}
                >
                  <CardHeader className="py-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{clause.clause_type.replace('_', ' ').toUpperCase()}</CardTitle>
                      <Badge variant={clause.is_present ? 'default' : 'secondary'}>
                        {clause.is_present ? 'Present' : 'Not Present'}
                      </Badge>
                    </div>
                  </CardHeader>
                  {clause.is_present && (
                    <CardContent className="pb-4 text-sm whitespace-pre-wrap">
                      {clause.clause_text}
                    </CardContent>
                  )}
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* RISKS TAB */}
        <TabsContent value="risks" className="space-y-4">
          {!risksData ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <p className="text-muted-foreground mb-4">No risks detected yet.</p>
                <Button onClick={handleDetectRisks} disabled={actionLoading || !clausesData}>
                  <Play className="mr-2 h-4 w-4" /> Run Risk Detection
                </Button>
                {!clausesData && <p className="text-xs text-muted-foreground mt-2">Requires Clauses to be extracted first.</p>}
              </CardContent>
            </Card>
          ) : risksData.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <CheckCircle2 className="h-12 w-12 text-primary mb-4" />
                <p className="text-lg font-medium">No major risks detected.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {risksData.map(risk => (
                <Card key={risk.id} className={risk.severity === 'high' ? 'border-destructive/50 shadow-sm' : ''}>
                  <CardHeader className="py-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                          {risk.severity === 'high' && <AlertTriangle className="h-4 w-4 text-destructive" />}
                          {risk.risk_type.replace('_', ' ').toUpperCase()}
                        </CardTitle>
                      </div>
                      <Badge variant={risk.severity === 'high' ? 'destructive' : (risk.severity === 'medium' ? 'default' : 'secondary')}>
                        {risk.severity.toUpperCase()}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pb-4 space-y-2 text-sm">
                    <div>
                      <span className="font-semibold block">Explanation:</span>
                      {risk.explanation}
                    </div>
                    <div>
                      <span className="font-semibold block">Recommendation:</span>
                      {risk.recommendation}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

      </Tabs>
    </div>
  );
}
