import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { searchApi } from '@/api/searchApi';
import { projectsApi } from '@/api/projectsApi';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Search as SearchIcon, FileText } from 'lucide-react';

export default function Search() {
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

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

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim() || !selectedProjectId) return;
    
    setSearching(true);
    setHasSearched(true);
    try {
      const res = await searchApi.semanticSearch(selectedProjectId, query);
      setResults(res.results || []);
    } catch (err) {
      alert("Search failed. Please try again.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="flex flex-col gap-8 max-w-4xl mx-auto w-full">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Ask Your Contracts</h1>
        <p className="text-muted-foreground mt-1">Search by meaning or ask questions across all contracts in a project.</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4 items-end">
            <div className="space-y-2 flex-1 w-full md:max-w-xs">
              <Label htmlFor="project">Select Project Scope</Label>
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
            
            <div className="space-y-2 flex-1 w-full">
              <Label htmlFor="query">Search Query</Label>
              <div className="flex gap-2">
                <Input
                  id="query"
                  placeholder="e.g. 'What is the termination notice period?'"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  required
                />
                <Button type="submit" disabled={searching || !query.trim()}>
                  <SearchIcon className="h-4 w-4 mr-2" />
                  Search
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {hasSearched && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Results ({results.length})</h2>
          
          {searching ? (
            <div className="text-muted-foreground">Searching documents...</div>
          ) : results.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground bg-muted/20 rounded-lg border">
              No matching semantic results found. Try rephrasing your query.
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {results.map((result, idx) => (
                <Card key={idx}>
                  <CardHeader className="py-4">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base flex items-center gap-2">
                        <FileText className="h-4 w-4 text-primary" />
                        <Link to={`/contracts/${result.contract_id}`} className="hover:underline">
                          {result.contract_filename}
                        </Link>
                      </CardTitle>
                      <div className="text-xs font-mono bg-muted px-2 py-1 rounded">
                        Score: {(result.similarity_score * 100).toFixed(1)}%
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="pb-4 pt-0">
                    <p className="text-sm text-muted-foreground">
                      <span className="font-semibold text-foreground">Page {result.page_number || 'N/A'}: </span>
                      "...{result.text_snippet}..."
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
