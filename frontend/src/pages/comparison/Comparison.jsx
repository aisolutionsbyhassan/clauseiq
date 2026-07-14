import React, { useState, useEffect } from 'react';
import { projectsApi } from '@/api/projectsApi';
import { contractsApi } from '@/api/contractsApi';
import { comparisonsApi } from '@/api/comparisonsApi';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Play, ArrowRightLeft } from 'lucide-react';

export default function Comparison() {
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  
  const [contracts, setContracts] = useState([]);
  const [contractAId, setContractAId] = useState('');
  const [contractBId, setContractBId] = useState('');
  
  const [history, setHistory] = useState([]);
  const [activeComparison, setActiveComparison] = useState(null);
  
  const [loading, setLoading] = useState(false);

  // Load Projects
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const data = await projectsApi.getProjects();
        setProjects(data.projects || []);
        if (data.projects?.length > 0) {
          setSelectedProjectId(data.projects[0].id);
        }
      } catch (err) {
        console.error("Failed to load projects", err);
      }
    };
    loadProjects();
  }, []);

  // Load Contracts & History when Project changes
  useEffect(() => {
    const loadProjectData = async () => {
      if (!selectedProjectId) return;
      try {
        const cRes = await contractsApi.getContracts(selectedProjectId);
        setContracts(cRes.contracts || []);
        setContractAId('');
        setContractBId('');
        setActiveComparison(null);
        
        const hRes = await comparisonsApi.listComparisons(selectedProjectId);
        setHistory(hRes.comparisons || []);
      } catch (err) {
        console.error("Failed to load project data", err);
      }
    };
    loadProjectData();
  }, [selectedProjectId]);

  const handleCompare = async (e) => {
    e.preventDefault();
    if (!selectedProjectId || !contractAId || !contractBId) return;
    if (contractAId === contractBId) {
      alert("Please select two different contracts to compare.");
      return;
    }
    
    setLoading(true);
    try {
      const res = await comparisonsApi.createComparison(selectedProjectId, contractAId, contractBId);
      setActiveComparison(res);
      // Prepend to history
      setHistory(prev => [res, ...prev]);
    } catch (err) {
      alert(err.response?.data?.detail || "Comparison failed. Make sure both contracts have extracted clauses.");
    } finally {
      setLoading(false);
    }
  };

  const loadPastComparison = async (comp) => {
    setActiveComparison(comp);
  };

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto w-full">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Contract Comparison</h1>
        <p className="text-muted-foreground mt-1">Select two contracts from the same project to semantically compare their clauses and obligations.</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleCompare} className="flex flex-col gap-4">
            <div className="space-y-2 w-full md:max-w-sm">
              <Label htmlFor="project">Project</Label>
              <select 
                id="project" 
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                required
              >
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            
            <div className="flex flex-col md:flex-row gap-4 items-end">
              <div className="space-y-2 flex-1">
                <Label>Original Contract (A)</Label>
                <select 
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={contractAId}
                  onChange={(e) => setContractAId(e.target.value)}
                  required
                >
                  <option value="" disabled>Select Contract A...</option>
                  {contracts.map(c => <option key={c.id} value={c.id}>{c.filename}</option>)}
                </select>
              </div>

              <div className="hidden md:flex mb-2 text-muted-foreground">
                <ArrowRightLeft className="h-6 w-6" />
              </div>

              <div className="space-y-2 flex-1">
                <Label>Modified Contract (B)</Label>
                <select 
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={contractBId}
                  onChange={(e) => setContractBId(e.target.value)}
                  required
                >
                  <option value="" disabled>Select Contract B...</option>
                  {contracts.map(c => <option key={c.id} value={c.id}>{c.filename}</option>)}
                </select>
              </div>
              
              <Button type="submit" disabled={loading || !contractAId || !contractBId}>
                <Play className="h-4 w-4 mr-2" />
                {loading ? 'Comparing...' : 'Compare'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results View */}
      {activeComparison && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold border-b pb-2">Comparison Results</h2>
          
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader className="bg-destructive/10 text-destructive rounded-t-lg">
                <CardTitle className="text-base">Removed Clauses</CardTitle>
                <CardDescription className="text-destructive/80">Found in A, missing in B</CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                {activeComparison.removed_clauses?.length ? (
                  <ul className="list-disc pl-5 space-y-2 text-sm">
                    {activeComparison.removed_clauses.map((c, i) => (
                      <li key={i}>
                        <span className="font-semibold">{c.clause_type || 'Clause'}:</span> {c.description}
                        {c.significance && <div className="text-muted-foreground text-xs mt-0.5">Impact: {c.significance}</div>}
                      </li>
                    ))}
                  </ul>
                ) : <span className="text-muted-foreground text-sm">None detected.</span>}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="bg-emerald-500/10 text-emerald-600 rounded-t-lg dark:text-emerald-400">
                <CardTitle className="text-base">Added Clauses</CardTitle>
                <CardDescription className="text-emerald-600/80 dark:text-emerald-400/80">Missing in A, found in B</CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                {activeComparison.added_clauses?.length ? (
                  <ul className="list-disc pl-5 space-y-2 text-sm">
                    {activeComparison.added_clauses.map((c, i) => (
                      <li key={i}>
                        <span className="font-semibold">{c.clause_type || 'Clause'}:</span> {c.description}
                        {c.significance && <div className="text-muted-foreground text-xs mt-0.5">Impact: {c.significance}</div>}
                      </li>
                    ))}
                  </ul>
                ) : <span className="text-muted-foreground text-sm">None detected.</span>}
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader className="bg-amber-500/10 text-amber-600 rounded-t-lg dark:text-amber-400">
                <CardTitle className="text-base">Modified Clauses</CardTitle>
                <CardDescription className="text-amber-600/80 dark:text-amber-400/80">Present in both, but substantively changed</CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                {activeComparison.modified_clauses?.length ? (
                  <ul className="list-disc pl-5 space-y-4 text-sm">
                    {activeComparison.modified_clauses.map((c, i) => (
                      <li key={i} className="border-b last:border-0 pb-4 last:pb-0">
                        <span className="font-semibold">{c.clause_type || 'Clause'}</span>
                        <div className="grid grid-cols-2 gap-2 mt-1">
                          <div className="bg-muted/50 p-2 rounded text-xs"><span className="font-medium">Before:</span> {c.before}</div>
                          <div className="bg-muted/50 p-2 rounded text-xs"><span className="font-medium">After:</span> {c.after}</div>
                        </div>
                        {c.significance && <div className="text-muted-foreground text-xs mt-1">Impact: {c.significance}</div>}
                      </li>
                    ))}
                  </ul>
                ) : <span className="text-muted-foreground text-sm">None detected.</span>}
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader className="bg-primary/10 text-primary rounded-t-lg">
                <CardTitle className="text-base">Changed Obligations</CardTitle>
                <CardDescription className="text-primary/80">Shifts in responsibility, timeline, or financial terms</CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                {activeComparison.changed_obligations?.length ? (
                  <ul className="list-disc pl-5 space-y-2 text-sm">
                    {activeComparison.changed_obligations.map((c, i) => (
                      <li key={i}>
                        <span className="font-semibold">{c.party || 'Party'}:</span> Changed from "{c.before}" to "{c.after}"
                        {c.impact && <div className="text-muted-foreground text-xs mt-0.5">Impact: {c.impact}</div>}
                      </li>
                    ))}
                  </ul>
                ) : <span className="text-muted-foreground text-sm">None detected.</span>}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Comparisons in Project</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-2">
              {history.map(comp => (
                <button 
                  key={comp.id}
                  onClick={() => loadPastComparison(comp)}
                  className="flex items-center justify-between p-3 rounded-md border hover:bg-muted/50 text-left transition-colors"
                >
                  <span className="text-sm font-medium">Comparison run on {new Date(comp.created_at).toLocaleDateString()}</span>
                  <span className="text-xs text-muted-foreground">View Result</span>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
