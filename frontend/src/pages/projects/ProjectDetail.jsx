import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { projectsApi } from '@/api/projectsApi';
import { contractsApi } from '@/api/contractsApi';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Upload, Trash2, FileText, ArrowLeft, Download } from 'lucide-react';

export default function ProjectDetail() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');

  const loadData = async () => {
    try {
      const proj = await projectsApi.getProject(projectId);
      setProject(proj);
      const res = await contractsApi.getContracts(projectId);
      setContracts(res.contracts || []);
    } catch (err) {
      console.error("Failed to load project details", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setUploadError('');
    try {
      await contractsApi.uploadContract(projectId, file);
      setIsUploadOpen(false);
      setFile(null);
      loadData();
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteProject = async () => {
    if (!window.confirm('Are you sure you want to delete this project? All contracts will be lost.')) return;
    try {
      await projectsApi.deleteProject(projectId);
      navigate('/projects');
    } catch (err) {
      alert('Failed to delete project');
    }
  };

  const handleDeleteContract = async (contractId) => {
    if (!window.confirm('Delete this contract?')) return;
    try {
      await contractsApi.deleteContract(contractId);
      loadData();
    } catch (err) {
      alert('Failed to delete contract');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-full">Loading...</div>;
  if (!project) return <div>Project not found.</div>;

  return (
    <div className="flex flex-col gap-8">
      <div>
        <Button variant="ghost" size="sm" className="mb-4 -ml-4" asChild>
          <Link to="/projects"><ArrowLeft className="mr-2 h-4 w-4" /> Back to Projects</Link>
        </Button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
            <p className="text-muted-foreground mt-1">{project.description || 'No description'}</p>
          </div>
          <div className="flex gap-2">
            <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
              <DialogTrigger asChild>
                <Button><Upload className="mr-2 h-4 w-4" /> Upload Contract</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Upload Contract</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleUpload} className="space-y-4 pt-4">
                  {uploadError && <div className="text-sm text-destructive">{uploadError}</div>}
                  <div className="space-y-2">
                    <Label htmlFor="file">Contract File (PDF or DOCX)</Label>
                    <Input
                      id="file"
                      type="file"
                      accept=".pdf,.docx"
                      onChange={(e) => setFile(e.target.files[0])}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={!file || uploading}>
                    {uploading ? 'Processing (this may take a minute)...' : 'Upload & Analyze'}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
            <Button variant="destructive" onClick={handleDeleteProject}>
              <Trash2 className="mr-2 h-4 w-4" /> Delete Project
            </Button>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Contracts in this Project</CardTitle>
        </CardHeader>
        <CardContent>
          {contracts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No contracts uploaded yet. Upload one to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-muted-foreground uppercase bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 font-medium">Filename</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium">Risk Level</th>
                    <th className="px-4 py-3 font-medium">Date Added</th>
                    <th className="px-4 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {contracts.map(c => (
                    <tr key={c.id} className="border-b last:border-0 hover:bg-muted/20">
                      <td className="px-4 py-3 font-medium">
                        <Link to={`/contracts/${c.id}`} className="flex items-center gap-2 hover:underline">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          {c.filename}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={c.processing_status === 'completed' ? 'default' : 'secondary'}>
                          {c.processing_status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={c.overall_risk_level === 'high' ? 'destructive' : 'outline'}>
                          {c.overall_risk_level}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {new Date(c.uploaded_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right space-x-2">
                        <Button variant="outline" size="sm" asChild>
                          <Link to={`/contracts/${c.id}`}>Analyze</Link>
                        </Button>
                        <Button variant="outline" size="sm" asChild>
                          <Link to={`/contracts/${c.id}/chat`}>Chat</Link>
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => contractsApi.downloadContract(c.id, c.filename)}>
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDeleteContract(c.id)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
