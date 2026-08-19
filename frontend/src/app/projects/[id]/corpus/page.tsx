"use client";
import { use } from 'react';

import { useEffect, useState, useRef, ChangeEvent } from 'react';
import axios from 'axios';
import { Upload, FileText, Database, ShieldAlert, GitBranch, Crosshair, HardDrive, Hash, CheckCircle, ChevronDown, ChevronRight, Play, Target } from 'lucide-react';
import clsx from 'clsx';
import { Card, CardHeader } from '@/components/discovery/ui';
import { SeedCorpusResponse, SeedSchema } from '@/types/corpus';

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function CorpusManagerPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = Number(resolvedParams.id);
  
  const [corpora, setCorpora] = useState<SeedCorpusResponse[]>([]);
  const [selectedCorpus, setSelectedCorpus] = useState<SeedCorpusResponse | null>(null);
  const [seeds, setSeeds] = useState<SeedSchema[]>([]);
  const [uploading, setUploading] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchCorpora = async () => {
    try {
      const res = await axios.get<SeedCorpusResponse[]>(`${API}/api/v1/projects/${projectId}/corpora`);
      setCorpora(res.data);
      if (res.data.length > 0 && !selectedCorpus) {
        setSelectedCorpus(res.data[0]);
      } else if (res.data.length > 0 && selectedCorpus) {
        // Update selected corpus data
        const updated = res.data.find(c => c.id === selectedCorpus.id);
        if (updated) setSelectedCorpus(updated);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSeeds = async (corpusId: number) => {
    try {
      const res = await axios.get<SeedSchema[]>(`${API}/api/v1/projects/${projectId}/corpora/${corpusId}/seeds`);
      setSeeds(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchCorpora();
  }, [projectId]);

  useEffect(() => {
    if (selectedCorpus) {
      fetchSeeds(selectedCorpus.id);
    }
  }, [selectedCorpus?.id]);

  const handleCreateCorpus = async () => {
    const name = prompt("Enter corpus name:");
    if (!name) return;
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/corpora`, { name, description: "" });
      fetchCorpora();
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !selectedCorpus) return;
    
    setUploading(true);
    const files = Array.from(e.target.files);
    
    for (const file of files) {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('origin', 'UPLOAD');
      
      try {
        await axios.post(`${API}/api/v1/projects/${projectId}/corpora/${selectedCorpus.id}/seeds`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } catch (err) {
        console.error(`Failed to upload ${file.name}`, err);
      }
    }
    
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
    fetchCorpora();
    fetchSeeds(selectedCorpus.id);
  };

  const triggerMinimize = async (seed: SeedSchema) => {
    if (!selectedCorpus) return;
    try {
      await axios.post(`${API}/api/v1/projects/${projectId}/corpora/${selectedCorpus.id}/minimize`);
      alert("Minimization job queued!");
    } catch (e) {
      console.error(e);
    }
  };

  // Build Lineage Tree Map
  const roots = seeds.filter(s => !s.parent_seed_id);
  const childrenMap = new Map<number, SeedSchema[]>();
  seeds.forEach(s => {
    if (s.parent_seed_id) {
      if (!childrenMap.has(s.parent_seed_id)) childrenMap.set(s.parent_seed_id, []);
      childrenMap.get(s.parent_seed_id)!.push(s);
    }
  });

  const SeedNode = ({ seed, depth = 0 }: { seed: SeedSchema, depth?: number }) => {
    const children = childrenMap.get(seed.id) || [];
    const [expanded, setExpanded] = useState(true);

    return (
      <div className="text-sm">
        <div className={clsx("flex items-center gap-3 p-2 rounded hover:bg-zinc-800/50 group", depth > 0 && "border-l border-zinc-800 ml-4 pl-4")}>
          <div className="w-5 flex justify-center">
            {children.length > 0 ? (
              <button onClick={() => setExpanded(!expanded)} className="text-zinc-500 hover:text-zinc-300">
                {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              </button>
            ) : (
              <FileText className="w-4 h-4 text-zinc-600" />
            )}
          </div>
          
          <div className="flex-1 font-mono text-zinc-300">{seed.filename}</div>
          
          <div className="flex gap-4 text-xs text-zinc-500 w-[400px]">
            <span className={clsx("px-2 py-0.5 rounded-sm font-semibold", 
              seed.origin === 'UPLOAD' ? 'bg-blue-900/30 text-blue-400' : 
              seed.origin === 'MINIMIZED' ? 'bg-purple-900/30 text-purple-400' : 'bg-zinc-800 text-zinc-400'
            )}>{seed.origin}</span>
            <span className="w-24">{(seed.size / 1024).toFixed(1)} KB</span>
            <span className="font-mono text-zinc-600 truncate w-24" title={seed.hash}>{seed.hash.substring(0,8)}...</span>
            <div className="flex gap-2 w-16">
              {seed.discovered_coverage && <div title="Discovered New Coverage"><Target className="w-4 h-4 text-emerald-400" /></div>}
              {seed.triggered_crash && <div title="Triggered Crash"><ShieldAlert className="w-4 h-4 text-red-400" /></div>}
            </div>
          </div>
          
          <div className="w-24 flex justify-end opacity-0 group-hover:opacity-100 transition-opacity">
             <button onClick={() => triggerMinimize(seed)} className="px-2 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded text-xs flex items-center gap-1">
               <Crosshair className="w-3 h-3"/> Minimize
             </button>
          </div>
        </div>
        
        {expanded && children.map(child => (
          <SeedNode key={child.id} seed={child} depth={depth + 1} />
        ))}
      </div>
    );
  };

  return (
    <div className="p-6 max-w-7xl mx-auto flex gap-6 h-[calc(100vh-4rem)]">
      
      {/* Sidebar - Corpora List */}
      <div className="w-64 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider">Corpora</h2>
          <button onClick={handleCreateCorpus} className="text-blue-400 hover:text-blue-300 text-sm">+</button>
        </div>
        
        <div className="space-y-2 overflow-y-auto">
          {corpora.map(c => (
            <div 
              key={c.id} 
              onClick={() => setSelectedCorpus(c)}
              className={clsx(
                "p-3 rounded-lg border cursor-pointer",
                selectedCorpus?.id === c.id ? "bg-blue-600/10 border-blue-500" : "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
              )}
            >
              <div className="font-medium text-zinc-200">{c.name}</div>
              <div className="text-xs text-zinc-500 mt-1 flex items-center gap-2">
                <FileText className="w-3 h-3" /> {c.total_seeds} seeds
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col gap-6 overflow-hidden">
        {selectedCorpus ? (
          <>
            {/* Header Stats */}
            <div className="grid grid-cols-4 gap-4 shrink-0">
              <Card className="p-4 flex items-center gap-4">
                <div className="p-3 bg-zinc-800 rounded-lg"><Database className="w-5 h-5 text-zinc-400" /></div>
                <div>
                  <div className="text-xs text-zinc-500">Total Seeds</div>
                  <div className="text-xl font-bold text-zinc-100">{selectedCorpus.total_seeds}</div>
                </div>
              </Card>
              <Card className="p-4 flex items-center gap-4">
                <div className="p-3 bg-zinc-800 rounded-lg"><Hash className="w-5 h-5 text-zinc-400" /></div>
                <div>
                  <div className="text-xs text-zinc-500">Unique Hashes</div>
                  <div className="text-xl font-bold text-zinc-100">{selectedCorpus.unique_hashes}</div>
                </div>
              </Card>
              <Card className="p-4 flex items-center gap-4">
                <div className="p-3 bg-zinc-800 rounded-lg"><HardDrive className="w-5 h-5 text-zinc-400" /></div>
                <div>
                  <div className="text-xs text-zinc-500">Corpus Size</div>
                  <div className="text-xl font-bold text-zinc-100">{(selectedCorpus.total_bytes / 1024 / 1024).toFixed(2)} MB</div>
                </div>
              </Card>
              <Card className="p-4 flex items-center gap-4">
                <div className="p-3 bg-zinc-800 rounded-lg"><CheckCircle className="w-5 h-5 text-emerald-500" /></div>
                <div>
                  <div className="text-xs text-zinc-500">Coverage Seeds</div>
                  <div className="text-xl font-bold text-zinc-100">{selectedCorpus.coverage_seeds}</div>
                </div>
              </Card>
            </div>

            {/* Lineage Tree */}
            <Card className="flex-1 flex flex-col min-h-0">
              <div className="flex items-center justify-between p-4 border-b border-zinc-800">
                <div className="flex items-center gap-2 text-zinc-100 font-semibold">
                  <GitBranch className="w-5 h-5" /> Seed Lineage
                </div>
                <div>
                  <input type="file" multiple className="hidden" ref={fileInputRef} onChange={handleFileUpload} />
                  <button 
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm disabled:opacity-50"
                  >
                    <Upload className="w-4 h-4" /> {uploading ? 'Uploading...' : 'Upload Seeds'}
                  </button>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-1">
                {seeds.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-zinc-500">
                    <Database className="w-12 h-12 mb-4 opacity-20" />
                    <p>No seeds in this corpus.</p>
                    <p className="text-sm mt-1">Upload original input files to get started.</p>
                  </div>
                ) : (
                  roots.map(root => <SeedNode key={root.id} seed={root} />)
                )}
              </div>
            </Card>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-zinc-500">
            Select or create a corpus.
          </div>
        )}
      </div>
      
    </div>
  );
}
